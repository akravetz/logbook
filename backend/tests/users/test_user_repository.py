"""Test user repository with anyio and transaction isolation."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from workout_api.users.models import User
from workout_api.users.repository import UserRepository

# Mark all tests in this module as anyio tests
pytestmark = pytest.mark.anyio


@pytest.fixture
async def user_repository(session: AsyncSession):
    """Create UserRepository instance with injected session."""
    return UserRepository(session)


@pytest.fixture
def user_data():
    """Sample user data for testing."""
    return {
        "email_address": "test@example.com",
        "google_id": "google123",
        "name": "Test User",
        "profile_image_url": "https://example.com/profile.jpg",
        "is_active": True,
        "is_admin": False,
    }


@pytest.fixture
async def created_user(user_repository: UserRepository, user_data: dict):
    """Create a user in the database for testing."""
    user = await user_repository.create(user_data)
    return user


class TestUserRepository:
    """Test cases for UserRepository."""

    async def test_create_user(self, user_repository: UserRepository, user_data: dict):
        """Test user creation through repository."""
        # Act
        user = await user_repository.create(user_data)

        # Assert
        assert user.id is not None
        assert user.email_address == "test@example.com"
        assert user.google_id == "google123"
        assert user.name == "Test User"
        assert user.profile_image_url == "https://example.com/profile.jpg"
        assert user.is_active is True
        assert user.is_admin is False
        assert user.created_at is not None
        assert user.updated_at is not None

    async def test_get_by_id_success(
        self, user_repository: UserRepository, created_user: User
    ):
        """Test successful user retrieval by ID."""
        # Act
        found_user = await user_repository.get_by_id(created_user.id)

        # Assert
        assert found_user is not None
        assert found_user.id == created_user.id
        assert found_user.email_address == created_user.email_address

    async def test_get_by_id_not_found(self, user_repository: UserRepository):
        """Test user retrieval by non-existent ID."""
        # Act
        found_user = await user_repository.get_by_id(999)

        # Assert
        assert found_user is None

    async def test_get_by_email_success(
        self, user_repository: UserRepository, created_user: User
    ):
        """Test successful user retrieval by email."""
        # Act
        found_user = await user_repository.get_by_email("test@example.com")

        # Assert
        assert found_user is not None
        assert found_user.id == created_user.id
        assert found_user.email_address == "test@example.com"

    async def test_get_by_email_not_found(self, user_repository: UserRepository):
        """Test user retrieval by non-existent email."""
        # Act
        found_user = await user_repository.get_by_email("nonexistent@example.com")

        # Assert
        assert found_user is None

    async def test_get_by_google_id_success(
        self, user_repository: UserRepository, created_user: User
    ):
        """Test successful user retrieval by Google ID."""
        # Act
        found_user = await user_repository.get_by_google_id("google123")

        # Assert
        assert found_user is not None
        assert found_user.id == created_user.id
        assert found_user.google_id == "google123"

    async def test_get_by_google_id_not_found(self, user_repository: UserRepository):
        """Test user retrieval by non-existent Google ID."""
        # Act
        found_user = await user_repository.get_by_google_id("nonexistent_google_id")

        # Assert
        assert found_user is None

    async def test_update_user_success(
        self, user_repository: UserRepository, created_user: User
    ):
        """Test successful user update."""
        # Arrange
        update_data = {
            "name": "Updated Name",
            "profile_image_url": "https://example.com/new_profile.jpg",
        }

        # Act
        updated_user = await user_repository.update(created_user.id, update_data)

        # Assert
        assert updated_user is not None
        assert updated_user.id == created_user.id
        assert updated_user.name == "Updated Name"
        assert updated_user.profile_image_url == "https://example.com/new_profile.jpg"
        assert updated_user.email_address == created_user.email_address  # Unchanged

    async def test_update_user_with_empty_data(
        self, user_repository: UserRepository, created_user: User
    ):
        """Test user update with empty data."""
        # Act
        updated_user = await user_repository.update(created_user.id, {})

        # Assert
        assert updated_user is not None
        assert updated_user.id == created_user.id
        assert updated_user.name == created_user.name  # Unchanged

    async def test_update_user_filters_none_values(
        self, user_repository: UserRepository, created_user: User
    ):
        """Test user update filters out None values."""
        # Arrange
        update_data = {
            "name": "Updated Name",
            "profile_image_url": None,  # Should be filtered out
            "email_address": "",  # Should be filtered out
        }

        # Act
        updated_user = await user_repository.update(created_user.id, update_data)

        # Assert
        assert updated_user is not None
        assert updated_user.name == "Updated Name"
        assert (
            updated_user.profile_image_url == created_user.profile_image_url
        )  # Unchanged
        assert updated_user.email_address == created_user.email_address  # Unchanged

    async def test_update_user_not_found(self, user_repository: UserRepository):
        """Test user update with non-existent user ID."""
        # Act
        updated_user = await user_repository.update(999, {"name": "New Name"})

        # Assert
        assert updated_user is None

    async def test_soft_delete_success(
        self, user_repository: UserRepository, created_user: User
    ):
        """Test successful user soft delete."""
        # Act
        success = await user_repository.soft_delete(created_user.id)

        # Assert
        assert success is True

        # Verify user is deactivated
        found_user = await user_repository.get_by_id(created_user.id)
        assert found_user is not None
        assert found_user.is_active is False

    async def test_soft_delete_not_found(self, user_repository: UserRepository):
        """Test soft delete with non-existent user ID."""
        # Act
        success = await user_repository.soft_delete(999)

        # Assert
        assert success is False

    async def test_reactivate_success(
        self, user_repository: UserRepository, created_user: User
    ):
        """Test successful user reactivation."""
        # Arrange - First deactivate the user
        await user_repository.soft_delete(created_user.id)

        # Act
        success = await user_repository.reactivate(created_user.id)

        # Assert
        assert success is True

        # Verify user is reactivated
        found_user = await user_repository.get_by_id(created_user.id)
        assert found_user is not None
        assert found_user.is_active is True

    async def test_reactivate_not_found(self, user_repository: UserRepository):
        """Test reactivation with non-existent user ID."""
        # Act
        success = await user_repository.reactivate(999)

        # Assert
        assert success is False

    async def test_create_user_with_minimal_data(self, user_repository: UserRepository):
        """Test user creation with minimal required data."""
        # Arrange
        minimal_data = {
            "email_address": "minimal@example.com",
            "google_id": "minimal_google_id",
            "name": "Minimal User",
            "is_active": True,
        }

        # Act
        user = await user_repository.create(minimal_data)

        # Assert
        assert user.id is not None
        assert user.email_address == "minimal@example.com"
        assert user.google_id == "minimal_google_id"
        assert user.name == "Minimal User"
        assert user.profile_image_url is None
        assert user.is_active is True
        assert user.is_admin is False  # Default value
