"""Tests for Authlib-based Google OAuth 2.0 integration."""

from unittest.mock import AsyncMock, Mock

import pytest
from starlette.requests import Request

from workout_api.auth.authlib_google import (
    AuthlibGoogleManager,
    GoogleOAuthError,
    GoogleUserInfo,
)
from workout_api.core.config import Settings


@pytest.fixture
def test_settings():
    """Create test settings for Google OAuth."""
    return Settings(
        jwt_secret_key="test_secret_key_12345678901234567890",  # gitleaks:allow
        jwt_algorithm="HS256",
        access_token_expire_minutes=30,
        refresh_token_expire_days=7,
        database_url="postgresql://test:test@localhost/test",
        google_client_id="test_client_id",
        google_client_secret="test_client_secret",
        google_redirect_uri="http://localhost:8000/api/v1/auth/google/callback",
        google_discovery_url="https://accounts.google.com/.well-known/openid_configuration",
    )


@pytest.fixture
def authlib_google_manager(test_settings):
    """Create AuthlibGoogleManager instance for testing."""
    return AuthlibGoogleManager(test_settings)


@pytest.fixture
def mock_request():
    """Create a mock Starlette Request object."""
    mock_request = Mock(spec=Request)
    mock_request.session = {}
    return mock_request


@pytest.fixture
def mock_google_userinfo_response():
    """Mock Google userinfo response."""
    return {
        "id": "google_user_123",
        "email": "test@example.com",
        "name": "Test User",
        "picture": "https://example.com/avatar.jpg",
        "email_verified": True,
        "given_name": "Test",
        "family_name": "User",
    }


@pytest.fixture
def mock_oauth_token_response(mock_google_userinfo_response):
    """Mock OAuth token response with userinfo."""
    return {
        "access_token": "access_token_123",
        "refresh_token": "refresh_token_456",
        "token_type": "Bearer",
        "expires_in": 3600,
        "userinfo": mock_google_userinfo_response,
    }


class TestGoogleUserInfo:
    """Test GoogleUserInfo data container."""

    def test_create_valid_user_info(self, mock_google_userinfo_response):
        """Test creating GoogleUserInfo with valid data."""
        user_info = GoogleUserInfo(mock_google_userinfo_response)

        assert user_info.google_id == "google_user_123"
        assert user_info.email == "test@example.com"
        assert user_info.name == "Test User"
        assert user_info.picture == "https://example.com/avatar.jpg"
        assert user_info.email_verified is True
        assert user_info.given_name == "Test"
        assert user_info.family_name == "User"

    def test_create_minimal_user_info(self):
        """Test creating GoogleUserInfo with minimal data."""
        data = {
            "sub": "google_user_123",
            "email": "test@example.com",
            "email_verified": True,
        }
        user_info = GoogleUserInfo(data)

        assert user_info.google_id == "google_user_123"
        assert user_info.email == "test@example.com"
        assert user_info.email_verified is True
        assert user_info.name == ""
        assert user_info.picture == ""

    def test_is_valid_with_complete_data(self, mock_google_userinfo_response):
        """Test is_valid() with complete user data."""
        user_info = GoogleUserInfo(mock_google_userinfo_response)
        assert user_info.is_valid() is True

    def test_is_valid_without_email_verified(self):
        """Test is_valid() when email is not verified."""
        data = {
            "sub": "google_user_123",
            "email": "test@example.com",
            "email_verified": False,
        }
        user_info = GoogleUserInfo(data)
        assert user_info.is_valid() is True

    def test_is_valid_missing_required_fields(self):
        """Test is_valid() with missing required fields."""
        test_cases = [
            {"email": "test@example.com", "email_verified": True},  # Missing sub/id
            {"sub": "123", "email_verified": True},  # Missing email
        ]

        for data in test_cases:
            user_info = GoogleUserInfo(data)
            assert user_info.is_valid() is False

        # Test case where email_verified is missing but should still be valid
        # since current implementation only checks google_id and email
        data = {"sub": "123", "email": "test@example.com"}  # Missing email_verified
        user_info = GoogleUserInfo(data)
        assert user_info.is_valid() is True

    def test_to_dict(self, mock_google_userinfo_response):
        """Test converting GoogleUserInfo to dictionary."""
        user_info = GoogleUserInfo(mock_google_userinfo_response)
        data = user_info.to_dict()

        assert data["google_id"] == "google_user_123"
        assert data["email"] == "test@example.com"
        assert data["name"] == "Test User"
        assert data["picture"] == "https://example.com/avatar.jpg"
        assert data["email_verified"] is True
        assert data["given_name"] == "Test"
        assert data["family_name"] == "User"


class TestAuthlibGoogleManager:
    """Test AuthlibGoogleManager functionality."""

    def test_manager_initialization(self, authlib_google_manager, test_settings):
        """Test AuthlibGoogleManager initialization."""
        assert authlib_google_manager.client_id == test_settings.google_client_id
        assert (
            authlib_google_manager.client_secret == test_settings.google_client_secret
        )
        assert authlib_google_manager.redirect_uri == test_settings.google_redirect_uri
        assert (
            authlib_google_manager.discovery_url == test_settings.google_discovery_url
        )
        assert authlib_google_manager.scopes == ["openid", "email", "profile"]
        assert authlib_google_manager.oauth is not None

    @pytest.mark.anyio
    async def test_authorize_redirect_with_default_uri(
        self, authlib_google_manager, mock_request
    ):
        """Test generating authorization redirect with default URI."""
        # Mock the OAuth client's authorize_redirect method
        mock_redirect_response = Mock()
        mock_redirect_response.status_code = 302
        authlib_google_manager.oauth.google.authorize_redirect = AsyncMock(
            return_value=mock_redirect_response
        )

        result = await authlib_google_manager.authorize_redirect(mock_request)

        assert result == mock_redirect_response
        authlib_google_manager.oauth.google.authorize_redirect.assert_called_once_with(
            mock_request, authlib_google_manager.redirect_uri
        )

    @pytest.mark.anyio
    async def test_authorize_redirect_with_custom_uri(
        self, authlib_google_manager, mock_request
    ):
        """Test generating authorization redirect with custom URI."""
        custom_uri = "http://localhost:3000/callback"
        mock_redirect_response = Mock()
        authlib_google_manager.oauth.google.authorize_redirect = AsyncMock(
            return_value=mock_redirect_response
        )

        result = await authlib_google_manager.authorize_redirect(
            mock_request, custom_uri
        )

        assert result == mock_redirect_response
        authlib_google_manager.oauth.google.authorize_redirect.assert_called_once_with(
            mock_request, custom_uri
        )

    @pytest.mark.anyio
    async def test_authorize_redirect_error(self, authlib_google_manager, mock_request):
        """Test authorization redirect with error."""
        authlib_google_manager.oauth.google.authorize_redirect = AsyncMock(
            side_effect=Exception("OAuth error")
        )

        with pytest.raises(GoogleOAuthError, match="Failed to initiate OAuth flow"):
            await authlib_google_manager.authorize_redirect(mock_request)

    @pytest.mark.anyio
    async def test_authorize_access_token_success(
        self, authlib_google_manager, mock_request, mock_oauth_token_response
    ):
        """Test successful OAuth token exchange."""
        authlib_google_manager.oauth.google.authorize_access_token = AsyncMock(
            return_value=mock_oauth_token_response
        )

        result = await authlib_google_manager.authorize_access_token(mock_request)

        assert result["access_token"] == "access_token_123"
        assert result["refresh_token"] == "refresh_token_456"
        assert result["token_type"] == "Bearer"
        assert result["expires_in"] == 3600
        assert result["userinfo"] == mock_oauth_token_response["userinfo"]

        authlib_google_manager.oauth.google.authorize_access_token.assert_called_once_with(
            mock_request
        )

    @pytest.mark.anyio
    async def test_authorize_access_token_no_token(
        self, authlib_google_manager, mock_request
    ):
        """Test OAuth token exchange when no token returned."""
        authlib_google_manager.oauth.google.authorize_access_token = AsyncMock(
            return_value=None
        )

        with pytest.raises(GoogleOAuthError, match="Failed to receive access token"):
            await authlib_google_manager.authorize_access_token(mock_request)

    @pytest.mark.anyio
    async def test_authorize_access_token_no_userinfo(
        self, authlib_google_manager, mock_request
    ):
        """Test OAuth token exchange when no userinfo in response."""
        token_response = {
            "access_token": "access_token_123",
            "token_type": "Bearer",
            # Missing userinfo
        }
        authlib_google_manager.oauth.google.authorize_access_token = AsyncMock(
            return_value=token_response
        )

        with pytest.raises(
            GoogleOAuthError, match="Failed to retrieve user information"
        ):
            await authlib_google_manager.authorize_access_token(mock_request)

    @pytest.mark.anyio
    async def test_authorize_access_token_error(
        self, authlib_google_manager, mock_request
    ):
        """Test OAuth token exchange with error."""
        authlib_google_manager.oauth.google.authorize_access_token = AsyncMock(
            side_effect=Exception("Token error")
        )

        with pytest.raises(GoogleOAuthError, match="OAuth authentication failed"):
            await authlib_google_manager.authorize_access_token(mock_request)

    def test_parse_user_info_success(
        self, authlib_google_manager, mock_google_userinfo_response
    ):
        """Test successful user info parsing."""
        result = authlib_google_manager.parse_user_info(mock_google_userinfo_response)

        assert isinstance(result, GoogleUserInfo)
        assert result.google_id == "google_user_123"
        assert result.email == "test@example.com"
        assert result.name == "Test User"

    def test_parse_user_info_invalid(self, authlib_google_manager):
        """Test parsing invalid user info."""
        invalid_userinfo = {"email": "test@example.com"}  # Missing google_id

        with pytest.raises(
            GoogleOAuthError, match="Invalid user information from Google"
        ):
            authlib_google_manager.parse_user_info(invalid_userinfo)

    def test_parse_user_info_error(self, authlib_google_manager):
        """Test parsing user info with unexpected error."""
        # Pass invalid data type to trigger exception
        with pytest.raises(GoogleOAuthError, match="Failed to parse user information"):
            authlib_google_manager.parse_user_info(None)


class TestIntegrationScenarios:
    """Test integration scenarios with Authlib Google OAuth."""

    @pytest.mark.anyio
    async def test_full_oauth_flow(
        self, authlib_google_manager, mock_request, mock_oauth_token_response
    ):
        """Test complete OAuth flow from redirect to user info parsing."""
        # Mock the OAuth client methods
        mock_redirect_response = Mock()
        mock_redirect_response.status_code = 302
        authlib_google_manager.oauth.google.authorize_redirect = AsyncMock(
            return_value=mock_redirect_response
        )
        authlib_google_manager.oauth.google.authorize_access_token = AsyncMock(
            return_value=mock_oauth_token_response
        )

        # Step 1: Generate authorization redirect
        redirect_result = await authlib_google_manager.authorize_redirect(mock_request)
        assert redirect_result == mock_redirect_response

        # Step 2: Exchange code for tokens and get user info
        token_result = await authlib_google_manager.authorize_access_token(mock_request)
        assert token_result["access_token"] == "access_token_123"
        assert "userinfo" in token_result

        # Step 3: Parse user info
        user_info = authlib_google_manager.parse_user_info(token_result["userinfo"])
        assert user_info.google_id == "google_user_123"
        assert user_info.email == "test@example.com"
        assert user_info.is_valid()


class TestErrorHandling:
    """Test error handling scenarios."""

    @pytest.mark.anyio
    async def test_handle_authlib_oauth_error(
        self, authlib_google_manager, mock_request
    ):
        """Test handling of Authlib OAuth errors."""
        from authlib.common.errors import AuthlibBaseError

        authlib_google_manager.oauth.google.authorize_redirect = AsyncMock(
            side_effect=AuthlibBaseError("Authlib OAuth error")
        )

        with pytest.raises(GoogleOAuthError, match="Failed to initiate OAuth flow"):
            await authlib_google_manager.authorize_redirect(mock_request)

    @pytest.mark.anyio
    async def test_handle_network_error_during_token_exchange(
        self, authlib_google_manager, mock_request
    ):
        """Test handling network errors during token exchange."""
        import httpx

        authlib_google_manager.oauth.google.authorize_access_token = AsyncMock(
            side_effect=httpx.RequestError("Network error")
        )

        with pytest.raises(GoogleOAuthError, match="OAuth authentication failed"):
            await authlib_google_manager.authorize_access_token(mock_request)
