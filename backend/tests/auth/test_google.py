"""Tests for Google OAuth 2.0 integration."""

from unittest.mock import AsyncMock, Mock

import httpx
import pytest

from workout_api.auth.google import (
    GoogleOAuthError,
    GoogleOAuthManager,
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
def google_oauth_manager(test_settings):
    """Create GoogleOAuthManager instance for testing."""
    return GoogleOAuthManager(test_settings)


@pytest.fixture
def mock_http_client():
    """Create a mock HTTP client."""
    return AsyncMock(spec=httpx.AsyncClient)


@pytest.fixture
def google_oauth_manager_with_client(test_settings, mock_http_client):
    """Create GoogleOAuthManager with injected HTTP client."""
    return GoogleOAuthManager(test_settings, mock_http_client)


@pytest.fixture
def mock_google_tokeninfo_response():
    """Mock Google token info response."""
    return {
        "audience": "test_client_id",
        "user_id": "google_user_123",
        "email": "test@example.com",
        "scope": "openid email profile",
        "expires_in": 3600,
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
            {"email": "test@example.com", "email_verified": True},  # Missing sub
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


class TestGoogleOAuthManager:
    """Test GoogleOAuthManager functionality."""

    def test_manager_initialization(self, google_oauth_manager, test_settings):
        """Test GoogleOAuthManager initialization."""
        assert google_oauth_manager.client_id == test_settings.google_client_id
        assert google_oauth_manager.client_secret == test_settings.google_client_secret
        assert google_oauth_manager.redirect_uri == test_settings.google_redirect_uri
        assert google_oauth_manager.discovery_url == test_settings.google_discovery_url
        assert google_oauth_manager.scopes == ["openid", "email", "profile"]

    def test_generate_authorization_url_with_state(self, google_oauth_manager):
        """Test generating authorization URL with provided state."""
        test_state = "test_state_123"

        auth_url, state = google_oauth_manager.generate_authorization_url(test_state)

        assert state == test_state
        assert "https://accounts.google.com/o/oauth2/v2/auth" in auth_url
        assert f"state={test_state}" in auth_url
        assert "client_id=test_client_id" in auth_url
        assert "response_type=code" in auth_url
        assert "scope=openid+email+profile" in auth_url
        assert "access_type=offline" in auth_url
        assert "prompt=consent" in auth_url

    def test_generate_authorization_url_without_state(self, google_oauth_manager):
        """Test generating authorization URL without state (auto-generated)."""
        auth_url, state = google_oauth_manager.generate_authorization_url()

        assert state is not None
        assert len(state) > 0
        assert "https://accounts.google.com/o/oauth2/v2/auth" in auth_url
        assert f"state={state}" in auth_url

    @pytest.mark.anyio
    @pytest.mark.anyio
    async def test_exchange_code_for_tokens_success(
        self,
        google_oauth_manager_with_client,
        mock_http_client,
        mock_google_token_response,
    ):
        """Test successful authorization code exchange."""
        # Setup mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_google_token_response
        mock_http_client.post.return_value = mock_response

        tokens = await google_oauth_manager_with_client.exchange_code_for_tokens(
            "test_code", "test_state"
        )

        assert tokens["access_token"] == mock_google_token_response["access_token"]
        assert tokens["refresh_token"] == mock_google_token_response["refresh_token"]
        assert tokens["token_type"] == mock_google_token_response["token_type"]

        # Verify the HTTP call
        mock_http_client.post.assert_called_once()
        call_args = mock_http_client.post.call_args
        assert call_args[0][0] == "https://oauth2.googleapis.com/token"
        assert call_args[1]["data"]["code"] == "test_code"
        assert call_args[1]["data"]["client_id"] == "test_client_id"

    @pytest.mark.anyio
    async def test_exchange_code_for_tokens_http_error(
        self, google_oauth_manager_with_client, mock_http_client
    ):
        """Test authorization code exchange with HTTP error."""
        # Setup mock error response
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.text = "Invalid authorization code"
        mock_http_client.post.return_value = mock_response

        with pytest.raises(
            GoogleOAuthError, match="Failed to exchange authorization code"
        ):
            await google_oauth_manager_with_client.exchange_code_for_tokens(
                "invalid_code", "test_state"
            )

    @pytest.mark.anyio
    async def test_exchange_code_for_tokens_network_error(
        self, google_oauth_manager_with_client, mock_http_client
    ):
        """Test authorization code exchange with network error."""
        mock_http_client.post.side_effect = httpx.RequestError("Network error")

        with pytest.raises(
            GoogleOAuthError, match="Network error during authentication"
        ):
            await google_oauth_manager_with_client.exchange_code_for_tokens(
                "test_code", "test_state"
            )

    @pytest.mark.anyio
    async def test_exchange_code_for_tokens_missing_access_token(
        self, google_oauth_manager_with_client, mock_http_client
    ):
        """Test authorization code exchange with missing access token in response."""
        # Setup mock response without access_token
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "refresh_token": "refresh_123",
            "token_type": "Bearer",
        }
        mock_http_client.post.return_value = mock_response

        with pytest.raises(
            GoogleOAuthError, match="Invalid token response from Google"
        ):
            await google_oauth_manager_with_client.exchange_code_for_tokens(
                "test_code", "test_state"
            )

    @pytest.mark.anyio
    async def test_get_user_info_success(
        self,
        google_oauth_manager_with_client,
        mock_http_client,
        mock_google_userinfo_response,
    ):
        """Test successful user info retrieval."""
        # Setup mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_google_userinfo_response
        mock_http_client.get.return_value = mock_response

        user_info = await google_oauth_manager_with_client.get_user_info(
            "test_access_token"
        )

        assert isinstance(user_info, GoogleUserInfo)
        assert user_info.google_id == "google_user_123"
        assert user_info.email == "test@example.com"
        assert user_info.is_valid() is True

        # Verify the HTTP call
        mock_http_client.get.assert_called_once_with(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": "Bearer test_access_token"},
            timeout=30.0,
        )

    @pytest.mark.anyio
    async def test_get_user_info_http_error(
        self, google_oauth_manager_with_client, mock_http_client
    ):
        """Test user info retrieval with HTTP error."""
        # Setup mock error response
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.text = "Invalid access token"
        mock_http_client.get.return_value = mock_response

        with pytest.raises(
            GoogleOAuthError, match="Failed to retrieve user information"
        ):
            await google_oauth_manager_with_client.get_user_info("invalid_token")

    @pytest.mark.anyio
    async def test_get_user_info_invalid_data(
        self, google_oauth_manager_with_client, mock_http_client
    ):
        """Test user info retrieval with invalid user data."""
        # Setup mock response with invalid data
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "email": "test@example.com"
        }  # Missing required fields
        mock_http_client.get.return_value = mock_response

        with pytest.raises(
            GoogleOAuthError, match="Invalid user information from Google"
        ):
            await google_oauth_manager_with_client.get_user_info("test_access_token")

    @pytest.mark.anyio
    async def test_verify_token_success(
        self,
        google_oauth_manager_with_client,
        mock_http_client,
        mock_google_tokeninfo_response,
    ):
        """Test successful token verification."""
        # Setup mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_google_tokeninfo_response
        mock_http_client.get.return_value = mock_response

        token_info = await google_oauth_manager_with_client.verify_token(
            "test_access_token"
        )

        assert token_info["audience"] == "test_client_id"
        assert token_info["user_id"] == "google_user_123"
        assert token_info["email"] == "test@example.com"

    @pytest.mark.anyio
    async def test_verify_token_invalid(
        self, google_oauth_manager_with_client, mock_http_client
    ):
        """Test token verification with invalid token."""
        # Setup mock error response
        mock_response = Mock()
        mock_response.status_code = 400
        mock_http_client.get.return_value = mock_response

        with pytest.raises(GoogleOAuthError, match="Invalid access token"):
            await google_oauth_manager_with_client.verify_token("invalid_token")

    @pytest.mark.anyio
    async def test_verify_token_wrong_audience(
        self, google_oauth_manager_with_client, mock_http_client
    ):
        """Test token verification with wrong audience."""
        # Setup mock response with wrong audience
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "audience": "wrong_client_id",
            "user_id": "google_user_123",
            "email": "test@example.com",
        }
        mock_http_client.get.return_value = mock_response

        with pytest.raises(
            GoogleOAuthError, match="Token not issued for this application"
        ):
            await google_oauth_manager_with_client.verify_token("test_access_token")

    def test_validate_state_success(self, google_oauth_manager):
        """Test successful state validation."""
        assert google_oauth_manager.validate_state("test_state", "test_state") is True

    def test_validate_state_mismatch(self, google_oauth_manager):
        """Test state validation with mismatch."""
        assert google_oauth_manager.validate_state("state1", "state2") is False

    def test_validate_state_missing(self, google_oauth_manager):
        """Test state validation with missing state."""
        assert google_oauth_manager.validate_state("", "test_state") is False
        assert google_oauth_manager.validate_state("test_state", "") is False
        assert google_oauth_manager.validate_state(None, "test_state") is False
        assert google_oauth_manager.validate_state("test_state", None) is False


class TestIntegrationScenarios:
    """Test integration scenarios for Google OAuth."""

    @pytest.mark.anyio
    async def test_full_oauth_flow(
        self,
        google_oauth_manager_with_client,
        mock_http_client,
        mock_google_token_response,
        mock_google_userinfo_response,
    ):
        """Test complete OAuth flow from authorization to user info."""
        # Step 1: Generate authorization URL
        auth_url, state = google_oauth_manager_with_client.generate_authorization_url()
        assert auth_url and state

        # Step 2: Exchange code for tokens
        mock_token_response = Mock()
        mock_token_response.status_code = 200
        mock_token_response.json.return_value = mock_google_token_response
        mock_http_client.post.return_value = mock_token_response

        tokens = await google_oauth_manager_with_client.exchange_code_for_tokens(
            "auth_code", state
        )
        assert tokens["access_token"] == "mock_google_access_token"

        # Step 3: Get user info
        mock_userinfo_response = Mock()
        mock_userinfo_response.status_code = 200
        mock_userinfo_response.json.return_value = mock_google_userinfo_response
        mock_http_client.get.return_value = mock_userinfo_response

        user_info = await google_oauth_manager_with_client.get_user_info(
            tokens["access_token"]
        )
        assert user_info.email == "test@example.com"
        assert user_info.is_valid() is True

    @pytest.mark.anyio
    async def test_oauth_flow_with_network_issues(
        self, google_oauth_manager_with_client, mock_http_client
    ):
        """Test OAuth flow handling network issues gracefully."""
        # Simulate network error during token exchange
        mock_http_client.post.side_effect = httpx.ConnectError("Connection refused")

        with pytest.raises(GoogleOAuthError, match="Network error"):
            await google_oauth_manager_with_client.exchange_code_for_tokens(
                "auth_code", "state"
            )

        # Simulate timeout during user info retrieval
        mock_http_client.get.side_effect = httpx.TimeoutException("Request timeout")

        with pytest.raises(GoogleOAuthError, match="Network error"):
            await google_oauth_manager_with_client.get_user_info("access_token")


class TestErrorHandling:
    """Test error handling in Google OAuth."""

    @pytest.mark.anyio
    async def test_handle_unexpected_error_in_exchange(
        self, google_oauth_manager_with_client, mock_http_client
    ):
        """Test handling unexpected errors during token exchange."""
        mock_http_client.post.side_effect = Exception("Unexpected error")

        with pytest.raises(GoogleOAuthError, match="Authentication failed"):
            await google_oauth_manager_with_client.exchange_code_for_tokens(
                "code", "state"
            )

    @pytest.mark.anyio
    async def test_handle_unexpected_error_in_user_info(
        self, google_oauth_manager_with_client, mock_http_client
    ):
        """Test handling unexpected errors during user info retrieval."""
        mock_http_client.get.side_effect = Exception("Unexpected error")

        with pytest.raises(
            GoogleOAuthError, match="Failed to retrieve user information"
        ):
            await google_oauth_manager_with_client.get_user_info("token")

    @pytest.mark.anyio
    async def test_handle_json_decode_error(
        self, google_oauth_manager_with_client, mock_http_client
    ):
        """Test handling JSON decode errors."""
        # Setup mock response with invalid JSON
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_http_client.post.return_value = mock_response

        with pytest.raises(GoogleOAuthError):
            await google_oauth_manager_with_client.exchange_code_for_tokens(
                "code", "state"
            )
