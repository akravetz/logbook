"""Authentication service with business logic."""

import logging
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from ..shared.exceptions import AuthenticationError, DuplicateError, NotFoundError
from ..users.models import User
from ..users.repository import UserRepository
from .authlib_google import GoogleUserInfo
from .jwt import JWTManager, TokenPair

logger = logging.getLogger("workout_api.auth.service")


class AuthService:
    """Authentication service for handling login, logout, and user management."""

    def __init__(
        self,
        session: AsyncSession,
        jwt_manager: JWTManager,
        user_repository: UserRepository,
    ):
        self.session = session
        self.jwt_manager = jwt_manager
        self.user_repository = user_repository

    async def authenticate_with_google(
        self, google_user_info: GoogleUserInfo
    ) -> tuple[User, TokenPair]:
        """Authenticate or create user from Google OAuth and return user with tokens."""
        try:
            # Look for existing user by Google ID first
            user = await self.user_repository.get_by_google_id(
                google_user_info.google_id
            )

            if user:
                # Update existing user info if needed
                user = await self._update_user_from_google(user, google_user_info)
                logger.info(f"Existing user authenticated: {user.email_address}")
            else:
                # Check if user exists by email (account linking case)
                existing_user = await self.user_repository.get_by_email(
                    google_user_info.email
                )

                if existing_user:
                    # Link Google account to existing user
                    existing_user.google_id = google_user_info.google_id
                    existing_user.name = google_user_info.name or existing_user.name
                    existing_user.profile_image_url = (
                        google_user_info.picture or existing_user.profile_image_url
                    )

                    await self.session.commit()
                    # Refresh the object to ensure it stays attached to the session
                    await self.session.refresh(existing_user)
                    user = existing_user
                    logger.info(
                        f"Linked Google account to existing user: {user.email_address}"
                    )
                else:
                    # Create new user
                    user = await self._create_user_from_google(google_user_info)
                    logger.info(f"New user created: {user.email_address}")

            # Create JWT tokens
            tokens = self.jwt_manager.create_token_pair(user.id, user.email_address)

            return user, tokens

        except Exception as e:
            await self.session.rollback()
            logger.error(f"Authentication error: {e}")
            raise AuthenticationError(f"Authentication failed: {str(e)}") from e

    async def _create_user_from_google(self, google_info: GoogleUserInfo) -> User:
        """Create a new user from Google OAuth information."""
        try:
            # Create new user using repository
            user_data = {
                "email_address": google_info.email,
                "google_id": google_info.google_id,
                "name": google_info.name or google_info.email.split("@")[0],
                "profile_image_url": google_info.picture,
                "is_active": True,
                "is_admin": False,
            }

            user = await self.user_repository.create(user_data)
            await self.session.commit()
            # Refresh the object to ensure it stays attached to the session
            await self.session.refresh(user)

            logger.info(f"Created new user: {user.id} - {user.email_address}")
            return user

        except (DuplicateError, AuthenticationError):
            # Re-raise specific exceptions without wrapping
            raise
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to create user: {e}")
            raise DuplicateError("User already exists or creation failed") from e

    async def _update_user_from_google(
        self, user: User, google_info: GoogleUserInfo
    ) -> User:
        """Update existing user with latest Google information."""
        try:
            # Update user fields if they've changed
            updated = False

            if user.name != google_info.name and google_info.name:
                user.name = google_info.name
                updated = True

            if user.profile_image_url != google_info.picture and google_info.picture:
                user.profile_image_url = google_info.picture
                updated = True

            # Ensure user is active
            if not user.is_active:
                user.is_active = True
                updated = True

            if updated:
                await self.session.commit()
                await self.session.refresh(user)
                logger.debug(f"Updated user information: {user.email_address}")

            return user

        except (NotFoundError, AuthenticationError):
            # Re-raise specific exceptions without wrapping
            raise
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to update user: {e}")
            raise AuthenticationError("Failed to update user information") from e

    async def refresh_user_token(self, user_id: int) -> TokenPair:
        """Create new token pair for user (used for token refresh)."""
        try:
            # Get user from database using repository
            user = await self.user_repository.get_by_id(user_id)

            if not user:
                logger.warning(f"User {user_id} not found for token refresh")
                raise NotFoundError("User not found")

            if not user.is_active:
                logger.warning(f"Inactive user {user_id} attempted token refresh")
                raise AuthenticationError("User account is inactive")

            # Create new token pair
            tokens = self.jwt_manager.create_token_pair(user.id, user.email_address)

            logger.info(f"Refreshed tokens for user: {user.email_address}")
            return tokens

        except (NotFoundError, AuthenticationError):
            # Re-raise specific exceptions without wrapping
            raise
        except Exception as e:
            logger.error(f"Token refresh failed for user {user_id}: {e}")
            raise AuthenticationError("Token refresh failed") from e

    async def deactivate_user(self, user_id: int) -> bool:
        """Deactivate user account (soft delete)."""
        try:
            success = await self.user_repository.soft_delete(user_id)

            if not success:
                logger.warning(f"User {user_id} not found for deactivation")
                raise NotFoundError("User not found")

            await self.session.commit()
            logger.info(f"Deactivated user: {user_id}")
            return True

        except (NotFoundError, AuthenticationError):
            # Re-raise specific exceptions without wrapping
            raise
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to deactivate user {user_id}: {e}")
            raise AuthenticationError("Failed to deactivate user") from e

    async def get_user_profile(self, user_id: int) -> User:
        """Get user profile information."""
        try:
            user = await self.user_repository.get_by_id(user_id)

            if not user:
                logger.warning(f"User {user_id} not found")
                raise NotFoundError("User not found")

            return user

        except (NotFoundError, AuthenticationError):
            # Re-raise specific exceptions without wrapping
            raise
        except Exception as e:
            logger.error(f"Failed to get user profile {user_id}: {e}")
            raise AuthenticationError("Failed to retrieve user profile") from e

    async def update_user_profile(
        self, user_id: int, update_data: dict[str, Any]
    ) -> User:
        """Update user profile information."""
        try:
            # Filter to only allowed fields
            allowed_fields = {"name", "profile_image_url"}
            filtered_data = {
                key: value
                for key, value in update_data.items()
                if key in allowed_fields
            }

            user = await self.user_repository.update(user_id, filtered_data)

            if not user:
                logger.warning(f"User {user_id} not found for update")
                raise NotFoundError("User not found")

            await self.session.commit()
            # Refresh the object to ensure it stays attached to the session
            await self.session.refresh(user)
            logger.info(f"Updated user profile: {user.email_address}")
            return user

        except (NotFoundError, AuthenticationError):
            # Re-raise specific exceptions without wrapping
            raise
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to update user profile {user_id}: {e}")
            raise AuthenticationError("Failed to update user profile") from e

    async def validate_user_access(self, user_id: int) -> bool:
        """Validate that user exists and is active."""
        try:
            user = await self.user_repository.get_by_id(user_id)
            return user is not None and user.is_active

        except Exception as e:
            logger.error(f"Failed to validate user access {user_id}: {e}")
            return False


def get_auth_service(session: AsyncSession, jwt_manager: JWTManager) -> AuthService:
    """Factory function to create AuthService instance."""
    from ..users.repository import UserRepository

    user_repository = UserRepository(session)
    return AuthService(session, jwt_manager, user_repository)
