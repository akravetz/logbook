"""Shared fixtures and utilities for authentication tests."""

from typing import Any
from unittest.mock import patch

import pytest

from workout_api.auth.google import GoogleUserInfo
from workout_api.auth.jwt import JWTManager, TokenPair
from workout_api.core.config import Settings
from workout_api.users.models import User

# Mark all tests in this module as anyio tests
pytestmark = pytest.mark.anyio


@pytest.fixture
def mock_google_user_info() -> GoogleUserInfo:
    """Create mock Google user info for testing."""
    data = {
        "sub": "google_user_123",
        "email": "test@example.com",
        "name": "Test User",
        "picture": "https://example.com/avatar.jpg",
        "email_verified": True,
        "given_name": "Test",
        "family_name": "User",
    }
    return GoogleUserInfo(data)


@pytest.fixture
def test_user_data() -> dict[str, Any]:
    """Create test user data."""
    return {
        "id": 1,
        "email_address": "test@example.com",
        "google_id": "google_user_123",
        "name": "Test User",
        "profile_image_url": "https://example.com/avatar.jpg",
        "is_active": True,
        "is_admin": False,
    }


@pytest.fixture
def test_admin_user_data() -> dict[str, Any]:
    """Create test admin user data."""
    return {
        "id": 2,
        "email_address": "admin@example.com",
        "google_id": "google_admin_456",
        "name": "Admin User",
        "profile_image_url": "https://example.com/admin_avatar.jpg",
        "is_active": True,
        "is_admin": True,
    }


@pytest.fixture
async def test_user(session, test_user_data) -> User:
    """Create a test user in the database."""
    user = User(**test_user_data)
    session.add(user)
    await session.flush()  # Use flush instead of commit for transaction isolation
    await session.refresh(user)
    return user


@pytest.fixture
async def test_admin_user(session, test_admin_user_data) -> User:
    """Create a test admin user in the database."""
    user = User(**test_admin_user_data)
    session.add(user)
    await session.flush()  # Use flush instead of commit for transaction isolation
    await session.refresh(user)
    return user


@pytest.fixture
def test_settings() -> Settings:
    """Create test settings."""
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
def jwt_manager(test_settings) -> JWTManager:
    """Create JWT manager for testing."""
    return JWTManager(test_settings)


@pytest.fixture
def valid_token_pair(test_user_data, jwt_manager) -> TokenPair:
    """Create valid JWT token pair for testing."""
    return jwt_manager.create_token_pair(
        test_user_data["id"], test_user_data["email_address"]
    )


@pytest.fixture
def mock_google_token_response() -> dict[str, Any]:
    """Mock Google OAuth token response."""
    return {
        "access_token": "mock_google_access_token",
        "token_type": "Bearer",
        "expires_in": 3600,
        "refresh_token": "mock_google_refresh_token",
        "scope": "openid email profile",
        "id_token": "mock_id_token",
    }


@pytest.fixture
def mock_google_userinfo_response() -> dict[str, Any]:
    """Mock Google userinfo API response."""
    return {
        "sub": "google_user_123",
        "email": "test@example.com",
        "name": "Test User",
        "picture": "https://example.com/avatar.jpg",
        "email_verified": True,
        "given_name": "Test",
        "family_name": "User",
    }


@pytest.fixture
def mock_httpx_client():
    """Mock httpx.AsyncClient for Google API calls."""
    with patch("httpx.AsyncClient") as mock_client:
        yield mock_client
