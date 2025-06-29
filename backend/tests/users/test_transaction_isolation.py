"""Test transaction isolation between tests."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from workout_api.users.repository import UserRepository

# Mark all tests in this module as anyio tests
pytestmark = pytest.mark.anyio


@pytest.fixture
async def user_repository(session: AsyncSession):
    """Create UserRepository instance with injected session."""
    return UserRepository(session)


class TestTransactionIsolation:
    """Test cases to verify transaction isolation between tests."""

    async def test_create_user_first(self, user_repository: UserRepository):
        """Create a user - should not be visible in subsequent tests."""
        # Arrange
        user_data = {
            "email_address": "isolation1@example.com",
            "google_id": "isolation_google_1",
            "name": "Isolation Test User 1",
            "is_active": True,
        }

        # Act
        user = await user_repository.create(user_data)

        # Assert
        assert user.id is not None
        assert user.email_address == "isolation1@example.com"

        # Verify we can find the user within this test
        found_user = await user_repository.get_by_email("isolation1@example.com")
        assert found_user is not None
        assert found_user.id == user.id

    async def test_create_user_second(self, user_repository: UserRepository):
        """Create another user - previous test's user should not be visible."""
        # First, verify that the user from the previous test is not visible
        previous_user = await user_repository.get_by_email("isolation1@example.com")
        assert previous_user is None, (
            "User from previous test should not be visible due to transaction isolation"
        )

        # Arrange
        user_data = {
            "email_address": "isolation2@example.com",
            "google_id": "isolation_google_2",
            "name": "Isolation Test User 2",
            "is_active": True,
        }

        # Act
        user = await user_repository.create(user_data)

        # Assert
        assert user.id is not None
        assert user.email_address == "isolation2@example.com"

        # Verify we can find this user within this test
        found_user = await user_repository.get_by_email("isolation2@example.com")
        assert found_user is not None
        assert found_user.id == user.id

    async def test_create_user_third(self, user_repository: UserRepository):
        """Create a third user - previous tests' users should not be visible."""
        # Verify that users from previous tests are not visible
        user1 = await user_repository.get_by_email("isolation1@example.com")
        user2 = await user_repository.get_by_email("isolation2@example.com")
        assert user1 is None, "User from first test should not be visible"
        assert user2 is None, "User from second test should not be visible"

        # Arrange
        user_data = {
            "email_address": "isolation3@example.com",
            "google_id": "isolation_google_3",
            "name": "Isolation Test User 3",
            "is_active": True,
        }

        # Act
        user = await user_repository.create(user_data)

        # Assert
        assert user.id is not None
        assert user.email_address == "isolation3@example.com"

    async def test_multiple_users_within_single_test(
        self, user_repository: UserRepository
    ):
        """Create multiple users within a single test - all should be visible to each other."""
        # Create first user
        user1_data = {
            "email_address": "multi1@example.com",
            "google_id": "multi_google_1",
            "name": "Multi User 1",
            "is_active": True,
        }
        user1 = await user_repository.create(user1_data)

        # Create second user
        user2_data = {
            "email_address": "multi2@example.com",
            "google_id": "multi_google_2",
            "name": "Multi User 2",
            "is_active": True,
        }
        user2 = await user_repository.create(user2_data)

        # Both users should be visible within this test
        found_user1 = await user_repository.get_by_email("multi1@example.com")
        found_user2 = await user_repository.get_by_email("multi2@example.com")

        assert found_user1 is not None
        assert found_user1.id == user1.id
        assert found_user2 is not None
        assert found_user2.id == user2.id

        # Verify they have different IDs
        assert user1.id != user2.id

    async def test_clean_state_verification(self, user_repository: UserRepository):
        """Verify that each test starts with a clean database state."""
        # This test should see no users from any previous tests
        users = [
            await user_repository.get_by_email("isolation1@example.com"),
            await user_repository.get_by_email("isolation2@example.com"),
            await user_repository.get_by_email("isolation3@example.com"),
            await user_repository.get_by_email("multi1@example.com"),
            await user_repository.get_by_email("multi2@example.com"),
        ]

        # All should be None due to transaction isolation
        for user in users:
            assert user is None, "No users from previous tests should be visible"

        # Create a user to verify the database is working
        user_data = {
            "email_address": "clean@example.com",
            "google_id": "clean_google",
            "name": "Clean State User",
            "is_active": True,
        }

        user = await user_repository.create(user_data)
        assert user.id is not None
