"""Tests for JWT token management."""

from datetime import UTC, datetime, timedelta
from unittest.mock import Mock

import pytest

from workout_api.auth.jwt import (
    DefaultTimeProvider,
    JWTManager,
    TokenData,
    TokenPair,
)
from workout_api.core.config import Settings
from workout_api.shared.exceptions import AuthenticationError


class MockTimeProvider:
    """Mock time provider for testing."""

    def __init__(self, fixed_time: datetime):
        self.fixed_time = fixed_time

    def now(self) -> datetime:
        return self.fixed_time


@pytest.fixture
def test_settings():
    """Create test settings."""
    return Settings(
        jwt_secret_key="test_secret_key_12345678901234567890",  # gitleaks:allow
        jwt_algorithm="HS256",
        access_token_expire_minutes=30,
        refresh_token_expire_days=7,
        database_url="postgresql://test:test@localhost/test",
        google_client_id="test_client_id",
        google_client_secret="test_client_secret",
        google_redirect_uri="http://localhost:8080/callback",
    )


@pytest.fixture
def fixed_time():
    """Fixed time for testing."""
    return datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)


@pytest.fixture
def mock_time_provider(fixed_time):
    """Create mock time provider."""
    return MockTimeProvider(fixed_time)


@pytest.fixture
def jwt_manager(test_settings, mock_time_provider):
    """Create JWT manager with test settings and mock time provider."""
    return JWTManager(test_settings, mock_time_provider)


class TestJWTManager:
    """Test JWT manager functionality."""

    def test_create_access_token(self, jwt_manager):
        """Test access token creation."""
        token = jwt_manager.create_access_token(1, "test@example.com")

        assert isinstance(token, str)
        assert len(token) > 0

        # Verify token can be decoded
        token_data = jwt_manager.verify_token(token, "access")
        assert token_data.user_id == 1
        assert token_data.email == "test@example.com"
        assert token_data.token_type == "access"

    def test_create_refresh_token(self, jwt_manager):
        """Test refresh token creation."""
        token = jwt_manager.create_refresh_token(1, "test@example.com")

        assert isinstance(token, str)
        assert len(token) > 0

        # Verify token can be decoded
        token_data = jwt_manager.verify_token(token, "refresh")
        assert token_data.user_id == 1
        assert token_data.email == "test@example.com"
        assert token_data.token_type == "refresh"

    def test_create_token_pair(self, jwt_manager):
        """Test token pair creation."""
        token_pair = jwt_manager.create_token_pair(1, "test@example.com")

        assert isinstance(token_pair, TokenPair)
        assert token_pair.access_token
        assert token_pair.refresh_token
        assert token_pair.token_type == "Bearer"
        assert token_pair.expires_in == 30 * 60  # 30 minutes in seconds

    def test_verify_valid_token(self, jwt_manager):
        """Test verifying a valid token."""
        token = jwt_manager.create_access_token(1, "test@example.com")
        token_data = jwt_manager.verify_token(token, "access")

        assert token_data.user_id == 1
        assert token_data.email == "test@example.com"
        assert token_data.token_type == "access"
        # Just check that we have datetime objects
        assert isinstance(token_data.issued_at, datetime)
        assert isinstance(token_data.expires_at, datetime)

    def test_verify_invalid_token(self, jwt_manager):
        """Test verifying an invalid token."""
        with pytest.raises(AuthenticationError, match="Invalid token"):
            jwt_manager.verify_token("invalid_token", "access")

    def test_verify_wrong_token_type(self, jwt_manager):
        """Test verifying token with wrong type."""
        access_token = jwt_manager.create_access_token(1, "test@example.com")

        with pytest.raises(AuthenticationError, match="Invalid token type"):
            jwt_manager.verify_token(access_token, "refresh")

    def test_verify_expired_token(self, test_settings):
        """Test verifying an expired token."""
        # Create token with past time
        past_time = datetime(2023, 1, 1, 12, 0, 0, tzinfo=UTC)
        past_time_provider = MockTimeProvider(past_time)
        past_jwt_manager = JWTManager(test_settings, past_time_provider)

        token = past_jwt_manager.create_access_token(1, "test@example.com")

        # Try to verify with current time
        current_jwt_manager = JWTManager(test_settings)
        with pytest.raises(AuthenticationError, match="Token has expired"):
            current_jwt_manager.verify_token(token, "access")

    def test_refresh_access_token(self, jwt_manager):
        """Test refreshing access token."""
        # Create refresh token
        refresh_token = jwt_manager.create_refresh_token(1, "test@example.com")

        # Refresh access token
        new_access_token = jwt_manager.refresh_access_token(refresh_token)

        assert isinstance(new_access_token, str)
        assert new_access_token != refresh_token

        # Verify new access token
        token_data = jwt_manager.verify_token(new_access_token, "access")
        assert token_data.user_id == 1
        assert token_data.email == "test@example.com"
        assert token_data.token_type == "access"

    def test_refresh_with_invalid_token(self, jwt_manager):
        """Test refreshing with invalid refresh token."""
        with pytest.raises(AuthenticationError):
            jwt_manager.refresh_access_token("invalid_token")

    def test_refresh_with_access_token(self, jwt_manager):
        """Test refreshing with access token (should fail)."""
        access_token = jwt_manager.create_access_token(1, "test@example.com")

        with pytest.raises(AuthenticationError, match="Invalid token type"):
            jwt_manager.refresh_access_token(access_token)

    def test_get_token_info(self, jwt_manager):
        """Test getting token info without validation."""
        token = jwt_manager.create_access_token(1, "test@example.com")
        token_info = jwt_manager.get_token_info(token)

        assert token_info["user_id"] == "1"
        assert token_info["email"] == "test@example.com"
        assert token_info["token_type"] == "access"
        assert "issued_at" in token_info
        assert "expires_at" in token_info
        assert "jwt_id" in token_info

    def test_get_token_info_invalid_token(self, jwt_manager):
        """Test getting info from invalid token."""
        token_info = jwt_manager.get_token_info("invalid_token")

        assert token_info == {}


class TestTimeProvider:
    """Test time provider functionality."""

    def test_default_time_provider(self):
        """Test default time provider returns current time."""
        provider = DefaultTimeProvider()
        now = provider.now()

        assert isinstance(now, datetime)
        assert now.tzinfo == UTC

        # Check it's close to actual current time (within 1 second)
        actual_now = datetime.now(UTC)
        assert abs((actual_now - now).total_seconds()) < 1

    def test_mock_time_provider(self, fixed_time):
        """Test mock time provider returns fixed time."""
        provider = MockTimeProvider(fixed_time)

        assert provider.now() == fixed_time
        assert provider.now() == fixed_time  # Should always return same time


class TestTokenData:
    """Test TokenData model."""

    def test_token_data_creation(self):
        """Test TokenData model creation."""
        now = datetime.now(UTC)
        expires = now + timedelta(minutes=30)

        token_data = TokenData(
            user_id=1,
            email="test@example.com",
            token_type="access",
            issued_at=now,
            expires_at=expires,
        )

        assert token_data.user_id == 1
        assert token_data.email == "test@example.com"
        assert token_data.token_type == "access"
        assert token_data.issued_at == now
        assert token_data.expires_at == expires


class TestTokenPair:
    """Test TokenPair model."""

    def test_token_pair_creation(self):
        """Test TokenPair model creation."""
        token_pair = TokenPair(
            access_token="access_token",
            refresh_token="refresh_token",
            expires_in=1800,
        )

        assert token_pair.access_token == "access_token"
        assert token_pair.refresh_token == "refresh_token"
        assert token_pair.token_type == "Bearer"
        assert token_pair.expires_in == 1800

    def test_token_pair_custom_type(self):
        """Test TokenPair with custom token type."""
        token_pair = TokenPair(
            access_token="access_token",
            refresh_token="refresh_token",
            token_type="Custom",
            expires_in=1800,
        )

        assert token_pair.token_type == "Custom"


class TestErrorHandling:
    """Test error handling in JWT operations."""

    def test_create_token_with_invalid_key(self, mock_time_provider):
        """Test token creation with invalid settings."""
        # Create a mock settings object instead of trying to create an invalid Settings instance

        invalid_settings = Mock()
        invalid_settings.jwt_secret_key = None  # Invalid None secret
        invalid_settings.jwt_algorithm = "HS256"
        invalid_settings.access_token_expire_minutes = 30
        invalid_settings.refresh_token_expire_days = 7

        jwt_manager = JWTManager(invalid_settings, mock_time_provider)

        with pytest.raises(AuthenticationError, match="Failed to create access token"):
            jwt_manager.create_access_token(1, "test@example.com")

    def test_verify_token_with_wrong_secret(self, test_settings, mock_time_provider):
        """Test verifying token with wrong secret key."""
        # Create token with one secret
        jwt_manager = JWTManager(test_settings, mock_time_provider)
        token = jwt_manager.create_access_token(1, "test@example.com")

        # Try to verify with different secret
        wrong_settings = Settings(
            jwt_secret_key="wrong_secret_key_12345678901234567890",  # gitleaks:allow
            jwt_algorithm="HS256",
            access_token_expire_minutes=30,
            refresh_token_expire_days=7,
            database_url="postgresql://test:test@localhost/test",
            google_client_id="test",
            google_client_secret="test",
            google_redirect_uri="http://test",
        )

        jwt_manager_wrong = JWTManager(wrong_settings, mock_time_provider)

        with pytest.raises(AuthenticationError, match="Invalid token"):
            jwt_manager_wrong.verify_token(token, "access")
