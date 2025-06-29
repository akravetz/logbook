"""Auth-specific test fixtures."""

from typing import Any
from unittest.mock import patch

import pytest

# Mark all tests in this module as anyio tests
pytestmark = pytest.mark.anyio


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
        "id": "google_user_123",
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
