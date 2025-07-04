"""Authentication service with business logic."""

import logging

from sqlalchemy.ext.asyncio import AsyncSession

from ..shared.exceptions import AuthenticationError, NotFoundError
from ..users.models import User
from ..users.repository import UserRepository
from .google_verification import GoogleTokenInfo, GoogleTokenVerifier
from .jwt import JWTManager

logger = logging.getLogger("workout_api.auth.service")


class AuthService:
    """Authentication service for handling login, logout, and user management."""

    def __init__(
        self,
        session: AsyncSession,
        jwt_manager: JWTManager,
        user_repository: UserRepository,
        google_verifier: GoogleTokenVerifier | None = None,
    ):
        self.session = session
        self.jwt_manager = jwt_manager
        self.user_repository = user_repository
        self.google_verifier = google_verifier

    async def authenticate_with_verified_google_token(
        self, access_token: str
    ) -> tuple[User, str]:
        """Authenticate user with verified Google access token and return session token.

        This method properly verifies the Google token using Google's tokeninfo API
        and returns a simple session token for API access.

        Args:
            access_token: Google OAuth access token from Auth.js

        Returns:
            tuple[User, str]: User object and session token for API access

        Raises:
            AuthenticationError: If token verification or user creation fails
        """
        if not self.google_verifier:
            raise AuthenticationError("Google token verification not configured")

        try:
            # Verify token with Google's API
            token_info = await self.google_verifier.verify_access_token(access_token)

            # Look for existing user by email
            user = await self.user_repository.get_by_email(token_info.email)

            if user:
                # Update existing user with verified Google data
                user = await self._update_user_from_verified_google(user, token_info)
                logger.info(
                    f"Existing user authenticated with verified token: {user.email_address}"
                )
            else:
                # Create new user from verified Google data
                user = await self._create_user_from_verified_google(token_info)
                logger.info(
                    f"New user created from verified token: {user.email_address}"
                )

            # Create simple session token (just access token, no refresh needed)
            session_token = self.jwt_manager.create_access_token(
                user.id, user.email_address
            )

            return user, session_token

        except (NotFoundError, AuthenticationError):
            raise
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Verified Google authentication error: {e}")
            raise AuthenticationError(
                f"Verified Google authentication failed: {str(e)}"
            ) from e

    async def _create_user_from_verified_google(
        self, token_info: GoogleTokenInfo
    ) -> User:
        """Create a new user from verified Google token information."""
        try:
            # Create new user with verified data
            user_data = {
                "email_address": str(token_info.email),
                "google_id": token_info.user_id,  # Use Google's user ID
                "name": token_info.name or str(token_info.email).split("@")[0],
                "profile_image_url": token_info.picture,
                "is_active": True,
                "is_admin": False,
            }

            user = await self.user_repository.create(user_data)
            await self.session.commit()
            await self.session.refresh(user)

            logger.info(
                f"Created new user from verified Google token: {user.id} - {user.email_address}"
            )
            return user

        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to create user from verified Google data: {e}")
            raise AuthenticationError("Failed to create user account") from e

    async def _update_user_from_verified_google(
        self, user: User, token_info: GoogleTokenInfo
    ) -> User:
        """Update existing user with verified Google token information."""
        try:
            # Update user with latest verified data, but don't overwrite existing data unnecessarily
            update_data = {}

            # Update Google ID if not set or different
            if not user.google_id or user.google_id != token_info.user_id:
                update_data["google_id"] = token_info.user_id

            # Update name if provided and different
            if token_info.name and user.name != token_info.name:
                update_data["name"] = token_info.name

            # Update profile image if provided and different
            if token_info.picture and user.profile_image_url != token_info.picture:
                update_data["profile_image_url"] = token_info.picture

            # Only update if there are changes
            if update_data:
                user = await self.user_repository.update(user.id, update_data)
                await self.session.commit()
                await self.session.refresh(user)
                logger.debug(
                    f"Updated user with verified Google data: {user.email_address}"
                )

            return user

        except (NotFoundError, AuthenticationError):
            raise
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to update user with verified Google data: {e}")
            raise AuthenticationError("Failed to update user information") from e
