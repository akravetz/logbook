"""Test user router with anyio and transaction isolation."""

from unittest.mock import AsyncMock

import pytest
from fastapi import status
from httpx import AsyncClient

from workout_api.auth.dependencies import get_current_user_from_token
from workout_api.core.main import app
from workout_api.users.models import User
from workout_api.users.service import UserService

# Mark all tests in this module as anyio tests
pytestmark = pytest.mark.anyio


@pytest.fixture
async def inactive_user(session):
    """Create an inactive user for testing."""
    user = User(
        email_address="inactive@example.com",
        google_id="google456",
        name="Inactive User",
        is_active=False,
    )
    session.add(user)
    await session.flush()
    await session.refresh(user)
    # Explicitly load all attributes to prevent lazy loading issues
    _ = (
        user.id,
        user.email_address,
        user.name,
        user.is_active,
        user.profile_image_url,
        user.google_id,
        user.is_admin,
        user.created_at,
        user.updated_at,
    )
    return user


@pytest.fixture
def mock_user_service():
    """Create a mock user service."""
    return AsyncMock(spec=UserService)


@pytest.fixture
async def authenticated_client(client: AsyncClient, test_user: User):
    """Create an authenticated client by overriding the auth dependency."""

    async def override_get_current_user():
        return test_user

    app.dependency_overrides[get_current_user_from_token] = override_get_current_user

    yield client

    # Clean up
    if get_current_user_from_token in app.dependency_overrides:
        del app.dependency_overrides[get_current_user_from_token]


class TestUserRouter:
    """Test cases for user API endpoints."""

    async def test_get_current_user_profile_success(
        self, authenticated_client: AsyncClient, test_user: User
    ):
        """Test successful current user profile retrieval."""
        # Extract user attributes early to avoid lazy loading issues
        user_id = test_user.id
        user_email = test_user.email_address
        user_name = test_user.name

        # Act
        response = await authenticated_client.get("/api/v1/users/me")

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == user_id
        assert data["email_address"] == user_email
        assert data["name"] == user_name

    async def test_get_current_user_profile_unauthenticated(self, client: AsyncClient):
        """Test current user profile retrieval without authentication."""
        # Act
        response = await client.get("/api/v1/users/me")

        # Assert - FastAPI returns 403 when no credentials are provided with HTTPBearer
        assert response.status_code == status.HTTP_403_FORBIDDEN

    async def test_get_current_user_profile_user_not_found(
        self,
        client: AsyncClient,
        mock_user_service,  # noqa: ARG002
    ):
        """Test current user profile retrieval when user not found."""
        # Create a mock user that doesn't exist in the database
        nonexistent_user = User(
            id=999,
            email_address="nonexistent@example.com",
            google_id="nonexistent",
            name="Nonexistent User",
            is_active=True,
        )

        # Override auth to return a user that doesn't exist in service
        async def override_get_current_user():
            return nonexistent_user

        app.dependency_overrides[get_current_user_from_token] = (
            override_get_current_user
        )

        try:
            # Act
            response = await client.get("/api/v1/users/me")

            # Assert
            assert response.status_code == status.HTTP_404_NOT_FOUND
        finally:
            # Clean up
            if get_current_user_from_token in app.dependency_overrides:
                del app.dependency_overrides[get_current_user_from_token]

    async def test_update_current_user_profile_success(
        self, authenticated_client: AsyncClient, test_user: User
    ):
        """Test successful current user profile update."""
        # Extract user attributes early to avoid lazy loading issues
        user_id = test_user.id

        # Arrange
        update_data = {
            "name": "Updated Name",
            "profile_image_url": "https://example.com/new_profile.jpg",
        }

        # Act
        response = await authenticated_client.patch(
            "/api/v1/users/me", json=update_data
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == user_id
        assert data["name"] == "Updated Name"
        assert data["profile_image_url"] == "https://example.com/new_profile.jpg"

    async def test_update_current_user_profile_empty_name(
        self, authenticated_client: AsyncClient
    ):
        """Test current user profile update with empty name."""
        # Arrange
        update_data = {"name": ""}

        # Act
        response = await authenticated_client.patch(
            "/api/v1/users/me", json=update_data
        )

        # Assert
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    async def test_update_current_user_profile_invalid_url(
        self, authenticated_client: AsyncClient
    ):
        """Test current user profile update with invalid URL."""
        # Arrange
        update_data = {"profile_image_url": "not-a-valid-url"}

        # Act
        response = await authenticated_client.patch(
            "/api/v1/users/me", json=update_data
        )

        # Assert
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    async def test_update_current_user_profile_unauthenticated(
        self, client: AsyncClient
    ):
        """Test current user profile update without authentication."""
        # Arrange
        update_data = {"name": "New Name"}

        # Act
        response = await client.patch("/api/v1/users/me", json=update_data)

        # Assert - FastAPI returns 403 when no credentials are provided with HTTPBearer
        assert response.status_code == status.HTTP_403_FORBIDDEN

    async def test_get_user_statistics_success(
        self,
        authenticated_client: AsyncClient,
        test_user: User,  # noqa: ARG002
    ):
        """Test successful user statistics retrieval."""
        # Act
        response = await authenticated_client.get("/api/v1/users/me/stats")

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "total_workouts" in data
        assert "total_exercises_performed" in data
        assert "total_sets" in data
        assert "total_weight_lifted" in data
        assert "workout_frequency" in data
        assert "most_performed_exercises" in data
        assert "body_part_distribution" in data
        assert "personal_records" in data
        assert "streak_info" in data

    async def test_get_user_statistics_with_date_range(
        self, authenticated_client: AsyncClient
    ):
        """Test user statistics retrieval with date range parameters."""
        # Act
        response = await authenticated_client.get(
            "/api/v1/users/me/stats",
            params={
                "start_date": "2024-01-01T00:00:00",
                "end_date": "2024-12-31T23:59:59",
            },
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK

    async def test_get_user_statistics_invalid_date_range(
        self, authenticated_client: AsyncClient
    ):
        """Test user statistics retrieval with invalid date range."""
        # Act
        response = await authenticated_client.get(
            "/api/v1/users/me/stats",
            params={
                "start_date": "2024-12-31T23:59:59",
                "end_date": "2024-01-01T00:00:00",
            },
        )

        # Assert - API correctly validates date range and returns 422
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert "Start date must be before end date" in response.json()["detail"]

    async def test_get_user_statistics_unauthenticated(self, client: AsyncClient):
        """Test user statistics retrieval without authentication."""
        # Act
        response = await client.get("/api/v1/users/me/stats")

        # Assert - FastAPI returns 403 when no credentials are provided with HTTPBearer
        assert response.status_code == status.HTTP_403_FORBIDDEN

    async def test_deactivate_current_user_success(
        self,
        authenticated_client: AsyncClient,
        test_user: User,  # noqa: ARG002
    ):
        """Test successful current user deactivation."""
        # Act
        response = await authenticated_client.delete("/api/v1/users/me")

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["message"] == "Account deactivated successfully"

    async def test_deactivate_current_user_unauthenticated(self, client: AsyncClient):
        """Test current user deactivation without authentication."""
        # Act
        response = await client.delete("/api/v1/users/me")

        # Assert - FastAPI returns 403 when no credentials are provided with HTTPBearer
        assert response.status_code == status.HTTP_403_FORBIDDEN

    async def test_endpoints_content_type_json(self, authenticated_client: AsyncClient):
        """Test that endpoints return JSON content type."""
        # Test GET profile
        response = await authenticated_client.get("/api/v1/users/me")
        assert response.headers["content-type"] == "application/json"

        # Test GET stats
        response = await authenticated_client.get("/api/v1/users/me/stats")
        assert response.headers["content-type"] == "application/json"

        # Test PATCH profile
        response = await authenticated_client.patch(
            "/api/v1/users/me", json={"name": "Test"}
        )
        assert response.headers["content-type"] == "application/json"

    async def test_patch_profile_partial_update(
        self, authenticated_client: AsyncClient, test_user: User
    ):
        """Test partial profile update with only one field."""
        # Extract user attributes early to avoid lazy loading issues
        user_email = test_user.email_address

        # Arrange - Update only name
        update_data = {"name": "Only Name Updated"}

        # Act
        response = await authenticated_client.patch(
            "/api/v1/users/me", json=update_data
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == "Only Name Updated"
        assert data["email_address"] == user_email  # Should remain unchanged

    async def test_patch_profile_empty_body(
        self, authenticated_client: AsyncClient, test_user: User
    ):
        """Test profile update with empty request body."""
        # Extract user attributes early to avoid lazy loading issues
        user_name = test_user.name

        # Act
        response = await authenticated_client.patch("/api/v1/users/me", json={})

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == user_name  # Should remain unchanged

    async def test_patch_profile_null_values(
        self, authenticated_client: AsyncClient, test_user: User
    ):
        """Test profile update with null values."""
        # Extract user attributes early to avoid lazy loading issues
        user_name = test_user.name

        # Arrange
        update_data = {"name": None, "profile_image_url": None}

        # Act
        response = await authenticated_client.patch(
            "/api/v1/users/me", json=update_data
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == user_name  # Should remain unchanged
