"""Test auth router endpoints with anyio and transaction isolation."""

from datetime import UTC, datetime, timedelta

import pytest
from fastapi import status
from httpx import AsyncClient
from httpx._transports.asgi import ASGITransport

from workout_api.auth.dependencies import (
    get_current_user_from_token,
    verify_token_only,
)
from workout_api.auth.jwt import TokenData
from workout_api.core.main import app
from workout_api.users.models import User

# Mark all tests in this module as anyio tests
pytestmark = pytest.mark.anyio


@pytest.fixture
def mock_token_data(test_user: User):
    """Create mock token data for testing."""
    # Extract user attributes early
    user_id = test_user.id
    user_email = test_user.email_address

    return TokenData(
        user_id=user_id,
        email=user_email,
        token_type="access",
        issued_at=datetime.now(UTC),
        expires_at=datetime.now(UTC) + timedelta(hours=1),
    )


@pytest.fixture
async def authenticated_client(
    client: AsyncClient, test_user: User, mock_token_data: TokenData
):
    """Create an authenticated client by overriding the auth dependencies."""

    async def override_get_current_user():
        return test_user

    def override_verify_token_only():
        return mock_token_data

    app.dependency_overrides[get_current_user_from_token] = override_get_current_user
    app.dependency_overrides[verify_token_only] = override_verify_token_only

    yield client

    # Clean up
    app.dependency_overrides.pop(get_current_user_from_token, None)
    app.dependency_overrides.pop(verify_token_only, None)


class TestAuthRouterValidation:
    """Test token validation endpoints."""

    async def test_validate_token_success(self, authenticated_client: AsyncClient):
        """Test successful token validation."""
        # Act
        response = await authenticated_client.get("/api/v1/auth/validate")

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["valid"] is True
        assert "user_id" in data
        assert "email" in data
        assert "expires_at" in data
        assert data["token_type"] == "access"

    async def test_validate_token_unauthenticated(self, client: AsyncClient):
        """Test token validation without authentication."""
        # Act
        response = await client.get("/api/v1/auth/validate")

        # Assert
        assert response.status_code == status.HTTP_403_FORBIDDEN

    async def test_validate_token_invalid_token(self, client: AsyncClient):
        """Test token validation with invalid token."""
        # Act
        response = await client.get(
            "/api/v1/auth/validate", headers={"Authorization": "Bearer invalid_token"}
        )

        # Assert
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestAuthRouterSession:
    """Test session management endpoints."""

    async def test_get_session_info_success(
        self, authenticated_client: AsyncClient, test_user: User
    ):
        """Test getting session info for authenticated user."""
        # Extract user attributes early to avoid lazy loading issues
        user_id = test_user.id
        user_email = test_user.email_address
        user_name = test_user.name
        user_profile_image = test_user.profile_image_url
        user_is_active = test_user.is_active

        # Act
        response = await authenticated_client.get("/api/v1/auth/me")

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["authenticated"] is True
        assert "user" in data
        user_data = data["user"]
        assert user_data["id"] == user_id
        assert user_data["email"] == user_email
        assert user_data["name"] == user_name
        assert user_data["profile_image_url"] == user_profile_image
        assert user_data["is_active"] == user_is_active

    async def test_get_session_info_admin_user(self, session):  # noqa: ARG002
        """Test session info includes admin status."""

        # Create admin user
        admin_user = User(
            id=999,
            email_address="admin@example.com",
            name="Admin User",
            google_id="admin_google_id",
            is_active=True,
            is_admin=True,
        )

        # Extract attributes early
        admin_id = admin_user.id
        admin_email = admin_user.email_address
        admin_name = admin_user.name

        token_data = TokenData(
            user_id=admin_id,
            email=admin_email,
            token_type="access",
            issued_at=datetime.now(UTC),
            expires_at=datetime.now(UTC) + timedelta(hours=1),
        )

        async def override_get_current_user():
            return admin_user

        def override_verify_token_only():
            return token_data

        app.dependency_overrides[get_current_user_from_token] = (
            override_get_current_user
        )
        app.dependency_overrides[verify_token_only] = override_verify_token_only

        try:
            # Create a client for this test
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                response = await client.get("/api/v1/auth/me")

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            user_data = data["user"]
            assert user_data["id"] == admin_id
            assert user_data["email"] == admin_email
            assert user_data["name"] == admin_name
            # Note: is_admin is not exposed in UserProfileResponse for security

        finally:
            app.dependency_overrides.pop(get_current_user_from_token, None)
            app.dependency_overrides.pop(verify_token_only, None)

    async def test_get_session_info_unauthenticated(self, client: AsyncClient):
        """Test getting session info without authentication."""
        # Act
        response = await client.get("/api/v1/auth/me")

        # Assert
        assert response.status_code == status.HTTP_403_FORBIDDEN

    async def test_logout_success(
        self,
        authenticated_client: AsyncClient,
        test_user: User,  # noqa: ARG002
    ):
        """Test successful logout."""
        # Act
        response = await authenticated_client.post("/api/v1/auth/logout")

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["logged_out"] is True
        assert "message" in data

    async def test_logout_unauthenticated(self, client: AsyncClient):
        """Test logout without authentication."""
        # Act
        response = await client.post("/api/v1/auth/logout")

        # Assert
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestAuthRouterEdgeCases:
    """Test edge cases and error conditions."""

    async def test_endpoints_require_authentication(self, client: AsyncClient):
        """Test that protected endpoints return 403 without authentication."""
        endpoints = [
            ("/api/v1/auth/me", "GET"),
            ("/api/v1/auth/logout", "POST"),
            ("/api/v1/auth/validate", "GET"),
        ]

        for endpoint, method in endpoints:
            if method == "GET":
                response = await client.get(endpoint)
            elif method == "POST":
                response = await client.post(endpoint)

            assert response.status_code == status.HTTP_403_FORBIDDEN

    async def test_all_endpoints_return_json(self, authenticated_client: AsyncClient):
        """Test that all endpoints return JSON content type."""
        endpoints = [
            ("/api/v1/auth/me", "GET"),
            ("/api/v1/auth/logout", "POST"),
            ("/api/v1/auth/validate", "GET"),
        ]

        for endpoint, method in endpoints:
            if method == "GET":
                response = await authenticated_client.get(endpoint)
            elif method == "POST":
                response = await authenticated_client.post(endpoint)

            assert response.status_code in [200, 201]
            assert "application/json" in response.headers.get("content-type", "")
