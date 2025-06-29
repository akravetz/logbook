"""User service for business logic."""

import logging
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from ..shared.exceptions import NotFoundError, ValidationError
from .repository import UserRepository
from .schemas import UserProfileUpdate, UserResponse, UserStatsResponse

logger = logging.getLogger(__name__)


class UserService:
    """Service for user business logic."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repository = UserRepository(session)

    async def get_user_profile(self, user_id: int) -> UserResponse:
        """Get user profile by ID."""
        user = await self.repository.get_by_id(user_id)
        if not user:
            raise NotFoundError(f"User with ID {user_id} not found")

        if not user.is_active:
            raise NotFoundError("User account is not active")

        # Convert to Pydantic model within session context
        return UserResponse.model_validate(user)

    async def update_user_profile(
        self, user_id: int, update_data: UserProfileUpdate
    ) -> UserResponse:
        """Update user profile with validation."""
        # Get current user to ensure they exist and are active
        current_user_response = await self.get_user_profile(user_id)

        # Convert Pydantic model to dict, excluding None values
        update_dict = update_data.model_dump(exclude_none=True)

        if not update_dict:
            # No data to update
            return current_user_response

        # Validate name if provided
        if "name" in update_dict:
            name = update_dict["name"].strip()
            if not name:
                raise ValidationError("Name cannot be empty")
            update_dict["name"] = name

        # Convert HttpUrl to string if profile_image_url is provided
        if "profile_image_url" in update_dict and update_dict["profile_image_url"]:
            update_dict["profile_image_url"] = str(update_dict["profile_image_url"])

        try:
            updated_user = await self.repository.update(user_id, update_dict)
            if not updated_user:
                raise NotFoundError(f"User with ID {user_id} not found")

            # Convert to Pydantic model BEFORE commit while session is still active
            user_response = UserResponse.model_validate(updated_user)

            await self.session.commit()
            logger.info(f"Updated profile for user {user_id}")

            return user_response

        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error updating user profile {user_id}: {e}")
            raise

    async def deactivate_user(self, user_id: int) -> bool:
        """Deactivate user account (soft delete)."""
        try:
            success = await self.repository.soft_delete(user_id)
            if success:
                await self.session.commit()
                logger.info(f"Deactivated user {user_id}")
            else:
                logger.warning(f"User {user_id} not found for deactivation")
            return success

        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error deactivating user {user_id}: {e}")
            raise

    async def reactivate_user(self, user_id: int) -> bool:
        """Reactivate user account."""
        try:
            success = await self.repository.reactivate(user_id)
            if success:
                await self.session.commit()
                logger.info(f"Reactivated user {user_id}")
            else:
                logger.warning(f"User {user_id} not found for reactivation")
            return success

        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error reactivating user {user_id}: {e}")
            raise

    async def get_user_statistics(
        self,
        user_id: int,
        start_date: datetime | None = None,  # noqa: ARG002
        end_date: datetime | None = None,  # noqa: ARG002
    ) -> UserStatsResponse:
        """Get user workout statistics."""
        # Ensure user exists and is active
        await self.get_user_profile(user_id)

        # For now, return mock data since we don't have workout data yet
        # This will be implemented when workout/exercise modules are ready
        logger.info(f"Getting statistics for user {user_id} (mock data)")

        return UserStatsResponse(
            total_workouts=0,
            total_exercises_performed=0,
            total_sets=0,
            total_weight_lifted=0.0,
            workout_frequency={"weekly_average": 0.0, "monthly_counts": {}},
            most_performed_exercises=[],
            body_part_distribution={},
            personal_records=[],
            streak_info={
                "current_streak": 0,
                "longest_streak": 0,
                "last_workout_date": None,
            },
        )

    async def check_user_exists(self, user_id: int) -> bool:
        """Check if user exists and is active."""
        try:
            user = await self.repository.get_by_id(user_id)
            return user is not None and user.is_active
        except Exception as e:
            logger.error(f"Error checking user existence {user_id}: {e}")
            return False
