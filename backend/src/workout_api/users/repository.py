"""User repository for database operations."""

import logging

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from .models import User

logger = logging.getLogger(__name__)


class UserRepository:
    """Repository for user database operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, user_id: int) -> User | None:
        """Get user by ID."""
        try:
            result = await self.session.get(User, user_id)
            return result
        except Exception as e:
            logger.error(f"Error getting user by ID {user_id}: {e}")
            raise

    async def get_by_email(self, email: str) -> User | None:
        """Get user by email address."""
        try:
            stmt = select(User).where(User.email_address == email)
            result = await self.session.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting user by email {email}: {e}")
            raise

    async def get_by_google_id(self, google_id: str) -> User | None:
        """Get user by Google ID."""
        try:
            stmt = select(User).where(User.google_id == google_id)
            result = await self.session.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting user by Google ID {google_id}: {e}")
            raise

    async def create(self, user_data: dict) -> User:
        """Create a new user."""
        try:
            user = User(**user_data)
            self.session.add(user)
            await self.session.flush()  # Get the ID without committing
            await self.session.refresh(user)
            logger.info(f"Created user with ID {user.id}")
            return user
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            raise

    async def update(self, user_id: int, update_data: dict) -> User | None:
        """Update user profile."""
        try:
            # Filter out None values and empty strings
            filtered_data = {
                key: value
                for key, value in update_data.items()
                if value is not None and value != ""
            }

            if not filtered_data:
                # No data to update, just return the current user
                return await self.get_by_id(user_id)

            stmt = (
                update(User)
                .where(User.id == user_id)
                .values(**filtered_data)
                .returning(User)
            )
            result = await self.session.execute(stmt)
            updated_user = result.scalar_one_or_none()

            if updated_user:
                logger.info(f"Updated user {user_id} with data: {filtered_data}")

            return updated_user
        except Exception as e:
            logger.error(f"Error updating user {user_id}: {e}")
            raise

    async def soft_delete(self, user_id: int) -> bool:
        """Soft delete user by setting is_active to False."""
        try:
            stmt = update(User).where(User.id == user_id).values(is_active=False)
            result = await self.session.execute(stmt)
            success = result.rowcount > 0

            if success:
                logger.info(f"Soft deleted user {user_id}")
            else:
                logger.warning(f"User {user_id} not found for soft delete")

            return success
        except Exception as e:
            logger.error(f"Error soft deleting user {user_id}: {e}")
            raise

    async def reactivate(self, user_id: int) -> bool:
        """Reactivate a soft-deleted user."""
        try:
            stmt = update(User).where(User.id == user_id).values(is_active=True)
            result = await self.session.execute(stmt)
            success = result.rowcount > 0

            if success:
                logger.info(f"Reactivated user {user_id}")
            else:
                logger.warning(f"User {user_id} not found for reactivation")

            return success
        except Exception as e:
            logger.error(f"Error reactivating user {user_id}: {e}")
            raise
