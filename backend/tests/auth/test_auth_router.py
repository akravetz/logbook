"""Test auth router endpoints with anyio and transaction isolation."""

from datetime import UTC
from unittest.mock import AsyncMock, Mock

import pytest
from fastapi import status
from httpx import AsyncClient
from httpx._transports.asgi import ASGITransport
from starlette.requests import Request

from workout_api.auth.authlib_google import AuthlibGoogleManager, GoogleUserInfo
from workout_api.auth.dependencies import (
    get_authlib_google_manager,
    get_current_user_from_token,
    get_jwt_manager,
    verify_token_only,
)
from workout_api.auth.jwt import JWTManager, TokenData
from workout_api.core.main import app
from workout_api.shared.exceptions import AuthenticationError
from workout_api.users.models import User

# Mark all tests in this module as anyio tests
pytestmark = pytest.mark.anyio


@pytest.fixture
def mock_token_data(test_user: User):
    """Create mock token data for testing."""
    # Extract user attributes early
    user_id = test_user.id
    user_email = test_user.email_address

    from datetime import datetime, timedelta

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


@pytest.fixture
def mock_google_oauth():
    """Create a mock AuthlibGoogleManager."""
    mock = AsyncMock(spec=AuthlibGoogleManager)
    return mock


@pytest.fixture
def mock_jwt_manager():
    """Create a mock JWTManager."""
    mock = Mock(spec=JWTManager)
    return mock


@pytest.fixture
def mock_request():
    """Create a mock Starlette Request."""
    mock = Mock(spec=Request)
    mock.url = Mock()
    mock.url.replace = Mock(return_value="https://example.com/auth/google/callback")
    return mock


@pytest.fixture
def sample_google_user_info():
    """Sample Google user info for testing."""
    return GoogleUserInfo(
        {
            "id": "google123",
            "email": "test@example.com",
            "name": "Test User",
            "picture": "https://example.com/profile.jpg",
            "email_verified": True,
        }
    )


@pytest.fixture
def sample_oauth_token_response():
    """Sample OAuth token response from Google."""
    return {
        "access_token": "access_token_123",
        "token_type": "Bearer",
        "expires_in": 3600,
        "refresh_token": "refresh_token_123",
        "userinfo": {
            "id": "google123",
            "email": "test@example.com",
            "name": "Test User",
            "picture": "https://example.com/profile.jpg",
        },
    }


class TestAuthRouterOAuth:
    """Test OAuth endpoints."""

    async def test_initiate_google_oauth_success(
        self, client: AsyncClient, mock_google_oauth
    ):
        """Test successful OAuth initiation."""
        # Arrange
        from starlette.responses import RedirectResponse

        mock_redirect_response = RedirectResponse(
            url="https://accounts.google.com/oauth/authorize?...", status_code=302
        )
        mock_google_oauth.authorize_redirect = AsyncMock(
            return_value=mock_redirect_response
        )

        # Override the dependency
        def override_get_authlib_google_manager():
            return mock_google_oauth

        app.dependency_overrides[get_authlib_google_manager] = (
            override_get_authlib_google_manager
        )

        try:
            # Act
            response = await client.get("/api/v1/auth/google")

            # Assert
            assert response.status_code == 302
            mock_google_oauth.authorize_redirect.assert_called_once()

        finally:
            # Clean up dependency override
            app.dependency_overrides.pop(get_authlib_google_manager, None)

    async def test_initiate_google_oauth_with_redirect_url(
        self, client: AsyncClient, mock_google_oauth
    ):
        """Test OAuth initiation with redirect URL parameter."""
        # Arrange
        from starlette.responses import RedirectResponse

        mock_redirect_response = RedirectResponse(
            url="https://accounts.google.com/oauth/authorize?...", status_code=302
        )
        mock_google_oauth.authorize_redirect = AsyncMock(
            return_value=mock_redirect_response
        )

        def override_get_authlib_google_manager():
            return mock_google_oauth

        app.dependency_overrides[get_authlib_google_manager] = (
            override_get_authlib_google_manager
        )

        try:
            # Act
            response = await client.get(
                "/api/v1/auth/google?redirect_url=https://example.com/dashboard"
            )

            # Assert
            assert response.status_code == 302
            mock_google_oauth.authorize_redirect.assert_called_once()

        finally:
            app.dependency_overrides.pop(get_authlib_google_manager, None)

    async def test_initiate_google_oauth_error(
        self, client: AsyncClient, mock_google_oauth
    ):
        """Test OAuth initiation with error."""
        # Arrange
        mock_google_oauth.authorize_redirect = AsyncMock(
            side_effect=Exception("OAuth service unavailable")
        )

        def override_get_authlib_google_manager():
            return mock_google_oauth

        app.dependency_overrides[get_authlib_google_manager] = (
            override_get_authlib_google_manager
        )

        try:
            # Act
            response = await client.get("/api/v1/auth/google")

            # Assert
            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            data = response.json()
            assert data["detail"] == "Failed to initiate authentication"

        finally:
            app.dependency_overrides.pop(get_authlib_google_manager, None)

    async def test_google_oauth_callback_success(
        self,
        client: AsyncClient,
        mock_google_oauth,
        sample_oauth_token_response,
        sample_google_user_info,
    ):
        """Test successful OAuth callback."""
        # Arrange
        mock_google_oauth.authorize_access_token = AsyncMock(
            return_value=sample_oauth_token_response
        )
        mock_google_oauth.parse_user_info = Mock(return_value=sample_google_user_info)

        def override_get_authlib_google_manager():
            return mock_google_oauth

        app.dependency_overrides[get_authlib_google_manager] = (
            override_get_authlib_google_manager
        )

        try:
            # Act
            response = await client.get(
                "/api/v1/auth/google/callback?code=auth_code&state=csrf_state"
            )

            # Assert
            assert response.status_code == status.HTTP_200_OK
            data = response.json()

            # Check response structure
            assert "user" in data
            assert "tokens" in data

            # Check user data
            user_data = data["user"]
            assert user_data["email_address"] == "test@example.com"
            assert user_data["name"] == "Test User"

            # Check tokens
            tokens = data["tokens"]
            assert "access_token" in tokens
            assert "refresh_token" in tokens
            assert tokens["token_type"] == "Bearer"

        finally:
            app.dependency_overrides.pop(get_authlib_google_manager, None)

    async def test_google_oauth_callback_with_error_param(self, client: AsyncClient):
        """Test OAuth callback with error parameter."""
        # Act
        response = await client.get(
            "/api/v1/auth/google/callback?error=access_denied&error_description=User%20denied%20access"
        )

        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert "OAuth error" in data["detail"]
        assert "User denied access" in data["detail"]

    async def test_google_oauth_callback_token_exchange_failure(
        self, client: AsyncClient, mock_google_oauth
    ):
        """Test OAuth callback when token exchange fails."""
        # Arrange
        mock_google_oauth.authorize_access_token = AsyncMock(
            side_effect=Exception("Token exchange failed")
        )

        def override_get_authlib_google_manager():
            return mock_google_oauth

        app.dependency_overrides[get_authlib_google_manager] = (
            override_get_authlib_google_manager
        )

        try:
            # Act
            response = await client.get(
                "/api/v1/auth/google/callback?code=auth_code&state=csrf_state"
            )

            # Assert
            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

        finally:
            app.dependency_overrides.pop(get_authlib_google_manager, None)

    async def test_google_oauth_callback_invalid_user_info(
        self, client: AsyncClient, mock_google_oauth, sample_oauth_token_response
    ):
        """Test OAuth callback with invalid user info."""
        # Arrange
        mock_google_oauth.authorize_access_token = AsyncMock(
            return_value=sample_oauth_token_response
        )
        mock_google_oauth.parse_user_info = Mock(
            side_effect=Exception("Invalid user info")
        )

        def override_get_authlib_google_manager():
            return mock_google_oauth

        app.dependency_overrides[get_authlib_google_manager] = (
            override_get_authlib_google_manager
        )

        try:
            # Act
            response = await client.get(
                "/api/v1/auth/google/callback?code=auth_code&state=csrf_state"
            )

            # Assert
            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

        finally:
            app.dependency_overrides.pop(get_authlib_google_manager, None)


class TestAuthRouterTokens:
    """Test token-related endpoints."""

    async def test_refresh_token_success(self, client: AsyncClient, mock_jwt_manager):
        """Test successful token refresh."""
        # Arrange
        refresh_token = "valid_refresh_token"
        new_access_token = "new_access_token"
        mock_jwt_manager.refresh_access_token = Mock(return_value=new_access_token)

        def override_get_jwt_manager():
            return mock_jwt_manager

        app.dependency_overrides[get_jwt_manager] = override_get_jwt_manager

        try:
            # Act
            response = await client.post(
                "/api/v1/auth/refresh", json={"refresh_token": refresh_token}
            )

            # Assert
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["access_token"] == new_access_token
            assert "expires_in" in data

            mock_jwt_manager.refresh_access_token.assert_called_once_with(refresh_token)

        finally:
            app.dependency_overrides.pop(get_jwt_manager, None)

    async def test_refresh_token_invalid_token(
        self, client: AsyncClient, mock_jwt_manager
    ):
        """Test token refresh with invalid refresh token."""
        # Arrange
        refresh_token = "invalid_refresh_token"
        mock_jwt_manager.refresh_access_token = Mock(
            side_effect=AuthenticationError("Invalid refresh token")
        )

        def override_get_jwt_manager():
            return mock_jwt_manager

        app.dependency_overrides[get_jwt_manager] = override_get_jwt_manager

        try:
            # Act
            response = await client.post(
                "/api/v1/auth/refresh", json={"refresh_token": refresh_token}
            )

            # Assert
            assert response.status_code == status.HTTP_401_UNAUTHORIZED
            data = response.json()
            assert "Invalid refresh token" in data["detail"]

        finally:
            app.dependency_overrides.pop(get_jwt_manager, None)

    async def test_refresh_token_missing_token(self, client: AsyncClient):
        """Test token refresh with missing refresh token."""
        # Act
        response = await client.post("/api/v1/auth/refresh", json={})

        # Assert
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    async def test_refresh_token_server_error(
        self, client: AsyncClient, mock_jwt_manager
    ):
        """Test token refresh with server error."""
        # Arrange
        refresh_token = "valid_refresh_token"
        mock_jwt_manager.refresh_access_token = Mock(
            side_effect=Exception("Database connection failed")
        )

        def override_get_jwt_manager():
            return mock_jwt_manager

        app.dependency_overrides[get_jwt_manager] = override_get_jwt_manager

        try:
            # Act
            response = await client.post(
                "/api/v1/auth/refresh", json={"refresh_token": refresh_token}
            )

            # Assert
            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

        finally:
            app.dependency_overrides.pop(get_jwt_manager, None)

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
    """Test session-related endpoints."""

    async def test_get_session_info_success(
        self, authenticated_client: AsyncClient, test_user: User
    ):
        """Test successful session info retrieval."""
        # Extract user attributes early to avoid lazy loading
        user_id = test_user.id
        user_email = test_user.email_address
        user_name = test_user.name

        # Act
        response = await authenticated_client.get("/api/v1/auth/me")

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["authenticated"] is True
        assert "user" in data
        assert "session_expires_at" in data
        assert "permissions" in data

        # Check user data
        user_data = data["user"]
        assert user_data["id"] == user_id
        assert user_data["email_address"] == user_email
        assert user_data["name"] == user_name

        # Check permissions
        assert "user" in data["permissions"]

    async def test_get_session_info_admin_user(self, session):
        """Test session info for admin user through the authenticated client."""
        # Create an admin user
        admin_user = User(
            email_address="admin@example.com",
            google_id="admin123",
            name="Admin User",
            is_active=True,
            is_admin=True,
        )
        session.add(admin_user)
        await session.flush()
        await session.refresh(admin_user)

        # Create token data for admin user
        from datetime import datetime, timedelta

        admin_token_data = TokenData(
            user_id=admin_user.id,
            email=admin_user.email_address,
            token_type="access",
            issued_at=datetime.now(UTC),
            expires_at=datetime.now(UTC) + timedelta(hours=1),
        )

        # Create authenticated client with admin user
        from httpx import AsyncClient

        client = AsyncClient(transport=ASGITransport(app), base_url="http://test")

        async def override_get_current_user():
            return admin_user

        def override_verify_token_only():
            return admin_token_data

        app.dependency_overrides[get_current_user_from_token] = (
            override_get_current_user
        )
        app.dependency_overrides[verify_token_only] = override_verify_token_only

        try:
            # Act
            response = await client.get("/api/v1/auth/me")

            # Assert
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert "user" in data["permissions"]
            assert "admin" in data["permissions"]

        finally:
            # Clean up
            app.dependency_overrides.pop(get_current_user_from_token, None)
            app.dependency_overrides.pop(verify_token_only, None)
            await client.aclose()

    async def test_get_session_info_unauthenticated(self, client: AsyncClient):
        """Test session info without authentication."""
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
        assert "Successfully logged out" in data["message"]

    async def test_logout_unauthenticated(self, client: AsyncClient):
        """Test logout without authentication."""
        # Act
        response = await client.post("/api/v1/auth/logout")

        # Assert
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestAuthRouterEdgeCases:
    """Test edge cases and error scenarios."""

    async def test_endpoints_require_authentication(self, client: AsyncClient):
        """Test that protected endpoints require authentication."""
        protected_endpoints = [
            ("GET", "/api/v1/auth/me"),
            ("POST", "/api/v1/auth/logout"),
            ("GET", "/api/v1/auth/validate"),
        ]

        for method, endpoint in protected_endpoints:
            if method == "GET":
                response = await client.get(endpoint)
            elif method == "POST":
                response = await client.post(endpoint)

            assert response.status_code == status.HTTP_403_FORBIDDEN

    async def test_oauth_callback_malformed_parameters(self, client: AsyncClient):
        """Test OAuth callback with malformed parameters."""
        # Act - missing code parameter
        response = await client.get("/api/v1/auth/google/callback?state=some_state")

        # Assert - should fail during token exchange
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_refresh_token_malformed_request(self, client: AsyncClient):
        """Test refresh token with malformed request."""
        # Act
        response = await client.post(
            "/api/v1/auth/refresh", json={"wrong_field": "value"}
        )

        # Assert
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    async def test_all_endpoints_return_json(self, authenticated_client: AsyncClient):
        """Test that all endpoints return JSON content."""
        endpoints = [
            ("GET", "/api/v1/auth/me"),
            ("POST", "/api/v1/auth/logout"),
            ("GET", "/api/v1/auth/validate"),
        ]

        for method, endpoint in endpoints:
            if method == "GET":
                response = await authenticated_client.get(endpoint)
            elif method == "POST":
                response = await authenticated_client.post(endpoint)

            assert response.headers.get("content-type", "").startswith(
                "application/json"
            )
