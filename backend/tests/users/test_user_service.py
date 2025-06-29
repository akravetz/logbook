"""Test user service with anyio and transaction isolation."""

from datetime import datetime

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from workout_api.shared.exceptions import NotFoundError, ValidationError
from workout_api.users.models import User
from workout_api.users.schemas import UserProfileUpdate
from workout_api.users.service import UserService

# Mark all tests in this module as anyio tests
pytestmark = pytest.mark.anyio


@pytest.fixture
async def user_service(session: AsyncSession):
    """Create UserService instance with injected session."""
    return UserService(session)


# Note: User fixtures are now provided by main conftest.py
# - test_user: Standard active user for testing
# - inactive_user: Inactive user for testing


class TestUserService:
    """Test cases for UserService."""

    async def test_get_user_profile_success(
        self, user_service: UserService, test_user: User
    ):
        """Test successful user profile retrieval."""
        # Act
        result = await user_service.get_user_profile(test_user.id)

        # Assert
        assert result.id == test_user.id
        assert result.email_address == "test@example.com"
        assert result.name == "Test User"
        assert result.is_active is True

    async def test_get_user_profile_not_found(self, user_service: UserService):
        """Test user profile retrieval with non-existent user."""
        # Act & Assert
        with pytest.raises(NotFoundError, match="User with ID 999 not found"):
            await user_service.get_user_profile(999)

    async def test_get_user_profile_inactive_user(
        self, user_service: UserService, inactive_user: User
    ):
        """Test user profile retrieval for inactive user."""
        # Act & Assert
        with pytest.raises(NotFoundError, match="User account is not active"):
            await user_service.get_user_profile(inactive_user.id)

    async def test_update_user_profile_success(
        self, user_service: UserService, test_user: User
    ):
        """Test successful user profile update."""
        # Arrange
        user_id = test_user.id
        original_email = test_user.email_address
        update_data = UserProfileUpdate(
            name="Updated Name", profile_image_url="https://example.com/new_profile.jpg"
        )

        # Act
        updated_user = await user_service.update_user_profile(user_id, update_data)

        # Assert - Check the returned values directly from the update
        assert updated_user is not None
        # Note: We avoid accessing lazy-loaded attributes after session is closed
        # Instead, we verify the update was successful by getting a fresh user
        fresh_user = await user_service.get_user_profile(user_id)
        assert fresh_user.name == "Updated Name"
        assert (
            str(fresh_user.profile_image_url) == "https://example.com/new_profile.jpg"
        )
        assert fresh_user.email_address == original_email  # Unchanged

    async def test_update_user_profile_empty_data(
        self, user_service: UserService, test_user: User
    ):
        """Test user profile update with no changes."""
        # Arrange
        user_id = test_user.id
        original_name = test_user.name
        update_data = UserProfileUpdate()

        # Act
        updated_user = await user_service.update_user_profile(user_id, update_data)

        # Assert
        assert updated_user is not None
        # Verify no changes by getting fresh user
        fresh_user = await user_service.get_user_profile(user_id)
        assert fresh_user.name == original_name  # Unchanged

    async def test_update_user_profile_empty_name(
        self,
        user_service: UserService,  # noqa: ARG002
        test_user: User,  # noqa: ARG002
    ):
        """Test user profile update with empty name."""
        # Act & Assert - Pydantic validation should catch this
        from pydantic import ValidationError as PydanticValidationError

        with pytest.raises(PydanticValidationError):
            UserProfileUpdate(name="")

    async def test_update_user_profile_whitespace_name(
        self, user_service: UserService, test_user: User
    ):
        """Test user profile update with whitespace-only name."""
        # Arrange - This should pass Pydantic validation but be caught by service layer
        update_data = UserProfileUpdate(name="   ")

        # Act & Assert
        with pytest.raises(ValidationError, match="Name cannot be empty"):
            await user_service.update_user_profile(test_user.id, update_data)

    async def test_update_user_profile_not_found(self, user_service: UserService):
        """Test user profile update for non-existent user."""
        # Arrange
        update_data = UserProfileUpdate(name="New Name")

        # Act & Assert
        with pytest.raises(NotFoundError, match="User with ID 999 not found"):
            await user_service.update_user_profile(999, update_data)

    async def test_deactivate_user_success(
        self, user_service: UserService, test_user: User
    ):
        """Test successful user deactivation."""
        # Act
        success = await user_service.deactivate_user(test_user.id)

        # Assert
        assert success is True

    async def test_deactivate_user_not_found(self, user_service: UserService):
        """Test user deactivation for non-existent user."""
        # Act
        success = await user_service.deactivate_user(999)

        # Assert
        assert success is False

    async def test_reactivate_user_success(
        self, user_service: UserService, inactive_user: User
    ):
        """Test successful user reactivation."""
        # Act
        success = await user_service.reactivate_user(inactive_user.id)

        # Assert
        assert success is True

    async def test_reactivate_user_not_found(self, user_service: UserService):
        """Test user reactivation for non-existent user."""
        # Act
        success = await user_service.reactivate_user(999)

        # Assert
        assert success is False

    async def test_get_user_statistics_success(
        self, user_service: UserService, test_user: User
    ):
        """Test successful user statistics retrieval."""
        # Act
        stats = await user_service.get_user_statistics(test_user.id)

        # Assert
        assert stats.total_workouts == 0  # Mock data
        assert stats.total_exercises_performed == 0
        assert stats.total_sets == 0
        assert stats.total_weight_lifted == 0.0
        assert stats.workout_frequency.weekly_average == 0.0
        assert stats.workout_frequency.monthly_counts == {}
        assert stats.most_performed_exercises == []
        assert stats.body_part_distribution == {}
        assert stats.personal_records == []
        assert stats.streak_info.current_streak == 0
        assert stats.streak_info.longest_streak == 0
        assert stats.streak_info.last_workout_date is None

    async def test_get_user_statistics_with_date_range(
        self, user_service: UserService, test_user: User
    ):
        """Test user statistics retrieval with date range."""
        # Arrange
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 12, 31)

        # Act
        stats = await user_service.get_user_statistics(
            test_user.id, start_date=start_date, end_date=end_date
        )

        # Assert - Should return mock data regardless of date range for now
        assert stats.total_workouts == 0

    async def test_get_user_statistics_user_not_found(self, user_service: UserService):
        """Test user statistics retrieval for non-existent user."""
        # Act & Assert
        with pytest.raises(NotFoundError, match="User with ID 999 not found"):
            await user_service.get_user_statistics(999)

    async def test_check_user_exists_active_user(
        self, user_service: UserService, test_user: User
    ):
        """Test checking existence of active user."""
        # Act
        exists = await user_service.check_user_exists(test_user.id)

        # Assert
        assert exists is True

    async def test_check_user_exists_inactive_user(
        self, user_service: UserService, inactive_user: User
    ):
        """Test checking existence of inactive user."""
        # Act
        exists = await user_service.check_user_exists(inactive_user.id)

        # Assert
        assert exists is False

    async def test_check_user_exists_not_found(self, user_service: UserService):
        """Test checking existence of non-existent user."""
        # Act
        exists = await user_service.check_user_exists(999)

        # Assert
        assert exists is False
