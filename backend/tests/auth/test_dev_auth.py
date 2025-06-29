"""Tests for development authentication functionality."""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from workout_api.core.config import Settings
from workout_api.shared.exceptions import AuthenticationError


class TestDevAuthentication:
    """Test development authentication features."""

    async def test_dev_login_success_in_development(self, client: TestClient, session):  # noqa: ARG002
        """Test successful development login when in development mode."""
        with patch("workout_api.core.config.get_settings") as mock_settings:
            # Mock development environment
            mock_settings.return_value = Settings(
                environment="development",
                database_url="sqlite:///test.db",
                secret_key="test-secret-key-with-at-least-32-characters",
                google_client_id="test-client-id",
                google_client_secret="test-client-secret",
            )

            response = await client.post(
                "/api/v1/auth/dev-login",
                json={"email": "test@example.com", "name": "Test User"},
            )

            assert response.status_code == 200
            data = response.json()

            # Verify response structure
            assert "user" in data
            assert "tokens" in data
            assert data["dev_mode"] is True

            # Verify user data
            user = data["user"]
            assert user["email_address"] == "test@example.com"
            assert user["name"] == "Test User"
            assert user["google_id"].startswith("dev:")
            assert user["is_active"] is True

            # Verify tokens
            tokens = data["tokens"]
            assert "access_token" in tokens
            assert "refresh_token" in tokens
            assert tokens["token_type"] == "Bearer"

    async def test_dev_login_with_existing_user(self, client: TestClient, session):  # noqa: ARG002
        """Test development login with existing user."""
        with patch("workout_api.core.config.get_settings") as mock_settings:
            # Mock development environment
            mock_settings.return_value = Settings(
                environment="development",
                database_url="sqlite:///test.db",
                secret_key="test-secret-key-with-at-least-32-characters",
                google_client_id="test-client-id",
                google_client_secret="test-client-secret",
            )

            # First request - creates user
            response1 = await client.post(
                "/api/v1/auth/dev-login",
                json={"email": "existing@example.com", "name": "First Name"},
            )
            assert response1.status_code == 200
            user_id_1 = response1.json()["user"]["id"]

            # Second request - should reuse existing user
            response2 = await client.post(
                "/api/v1/auth/dev-login",
                json={"email": "existing@example.com", "name": "Updated Name"},
            )
            assert response2.status_code == 200
            user_id_2 = response2.json()["user"]["id"]

            # Should be the same user ID
            assert user_id_1 == user_id_2

            # Name should be updated
            assert response2.json()["user"]["name"] == "Updated Name"

    async def test_dev_login_blocked_in_production(self, client: TestClient, session):  # noqa: ARG002
        """Test that development login is blocked in production mode."""
        with patch("workout_api.core.config.get_settings") as mock_settings:
            # Mock production environment
            mock_settings.return_value = Settings(
                environment="production",
                database_url="sqlite:///test.db",
                secret_key="test-secret-key-with-at-least-32-characters",
                google_client_id="test-client-id",
                google_client_secret="test-client-secret",
            )

            response = await client.post(
                "/api/v1/auth/dev-login",
                json={"email": "test@example.com", "name": "Test User"},
            )

            assert response.status_code == 401
            assert "development mode" in response.json()["detail"].lower()

    async def test_dev_login_minimal_data(self, client: TestClient, session):  # noqa: ARG002
        """Test development login with minimal data (email only)."""
        with patch("workout_api.core.config.get_settings") as mock_settings:
            # Mock development environment
            mock_settings.return_value = Settings(
                environment="development",
                database_url="sqlite:///test.db",
                secret_key="test-secret-key-with-at-least-32-characters",
                google_client_id="test-client-id",
                google_client_secret="test-client-secret",
            )

            response = await client.post(
                "/api/v1/auth/dev-login", json={"email": "minimal@example.com"}
            )

            assert response.status_code == 200
            data = response.json()

            # Should auto-generate name from email
            user = data["user"]
            assert user["email_address"] == "minimal@example.com"
            assert user["name"] == "minimal"  # Generated from email prefix

    async def test_dev_login_invalid_email(self, client: TestClient, session):  # noqa: ARG002
        """Test development login with invalid email format."""
        with patch("workout_api.core.config.get_settings") as mock_settings:
            # Mock development environment
            mock_settings.return_value = Settings(
                environment="development",
                database_url="sqlite:///test.db",
                secret_key="test-secret-key-with-at-least-32-characters",
                google_client_id="test-client-id",
                google_client_secret="test-client-secret",
            )

            response = await client.post(
                "/api/v1/auth/dev-login",
                json={"email": "not-an-email", "name": "Test User"},
            )

            assert response.status_code == 422  # Validation error


class TestDevAuthService:
    """Test the AuthService development authentication methods directly."""

    async def test_authenticate_with_dev_email_in_development(
        self,
        auth_service,
        session,  # noqa: ARG002
    ):
        """Test AuthService.authenticate_with_dev_email in development mode."""
        # Mock development settings
        auth_service.settings.environment = "development"

        user, tokens = await auth_service.authenticate_with_dev_email(
            email="service@example.com", name="Service User"
        )

        assert user.email_address == "service@example.com"
        assert user.name == "Service User"
        assert user.google_id == "dev:service@example.com"
        assert user.is_active is True
        assert tokens.access_token is not None
        assert tokens.refresh_token is not None

    async def test_authenticate_with_dev_email_blocked_in_production(
        self,
        auth_service,
        session,  # noqa: ARG002
    ):
        """Test AuthService.authenticate_with_dev_email blocked in production mode."""
        # Mock production settings
        auth_service.settings.environment = "production"

        with pytest.raises(AuthenticationError, match="development mode"):
            await auth_service.authenticate_with_dev_email(
                email="service@example.com", name="Service User"
            )
