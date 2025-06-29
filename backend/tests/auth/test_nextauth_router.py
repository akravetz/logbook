"""Tests for NextAuth.js integration endpoints."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from workout_api.auth.schemas import (
    NextAuthGoogleUserRequest,
    NextAuthVerificationResponse,
)
from workout_api.users.models import User

pytestmark = pytest.mark.anyio


class TestNextAuthIntegration:
    """Test NextAuth.js integration endpoints."""

    async def test_verify_google_user_new_user(self, client: AsyncClient):
        """Test creating new user via NextAuth.js."""
        request_data = {
            "email": "newuser@example.com",
            "name": "New User",
            "image": "https://example.com/avatar.jpg",
            "email_verified": True,
        }

        response = await client.post(
            "/api/v1/auth/verify-google-user", json=request_data
        )

        assert response.status_code == 200
        data = response.json()

        # Verify response structure matches schema
        assert "user" in data
        assert "tokens" in data

        # Verify user data
        user = data["user"]
        assert user["email"] == "newuser@example.com"
        assert user["name"] == "New User"
        assert user["image"] == "https://example.com/avatar.jpg"
        assert isinstance(user["id"], int)

        # Verify token data
        tokens = data["tokens"]
        assert "access_token" in tokens
        assert "refresh_token" in tokens
        assert "expires_in" in tokens
        assert isinstance(tokens["expires_in"], int)

    async def test_verify_google_user_existing_user(
        self,
        client: AsyncClient,
        test_user: User,  # noqa: ARG002
    ):
        """Test updating existing user via NextAuth.js."""
        # Use existing user's email but with updated information
        request_data = {
            "email": "test@example.com",
            "name": "Updated Name",
            "image": "https://example.com/new_avatar.jpg",
            "email_verified": True,
        }

        response = await client.post(
            "/api/v1/auth/verify-google-user", json=request_data
        )

        assert response.status_code == 200
        data = response.json()

        # Should update existing user
        user = data["user"]
        assert user["email"] == "test@example.com"
        assert user["name"] == "Updated Name"
        assert user["image"] == "https://example.com/new_avatar.jpg"

        # Should return valid tokens
        tokens = data["tokens"]
        assert "access_token" in tokens
        assert "refresh_token" in tokens

    async def test_verify_google_user_minimal_data(self, client: AsyncClient):
        """Test with minimal required data (only email)."""
        request_data = {
            "email": "minimal@example.com",
        }

        response = await client.post(
            "/api/v1/auth/verify-google-user", json=request_data
        )

        assert response.status_code == 200
        data = response.json()

        user = data["user"]
        assert user["email"] == "minimal@example.com"
        assert user["name"] == "minimal"  # Should default to email prefix
        assert user["image"] is None

    async def test_verify_google_user_validation_errors(self, client: AsyncClient):
        """Test validation errors for invalid requests."""
        # Missing required email
        response = await client.post(
            "/api/v1/auth/verify-google-user", json={"name": "Test User"}
        )

        assert response.status_code == 422
        error_data = response.json()
        assert "detail" in error_data
        assert any("email" in str(error).lower() for error in error_data["detail"])

        # Invalid email format
        response = await client.post(
            "/api/v1/auth/verify-google-user",
            json={"email": "invalid-email", "name": "Test User"},
        )

        assert response.status_code == 422

        # Invalid email_verified type
        response = await client.post(
            "/api/v1/auth/verify-google-user",
            json={"email": "test@example.com", "email_verified": "not_a_boolean"},
        )

        assert response.status_code == 422

    async def test_verify_google_user_empty_name_handling(self, client: AsyncClient):
        """Test handling of empty or null name fields."""
        # Null name
        request_data = {
            "email": "noname@example.com",
            "name": None,
        }

        response = await client.post(
            "/api/v1/auth/verify-google-user", json=request_data
        )

        assert response.status_code == 200
        data = response.json()
        user = data["user"]
        assert user["name"] == "noname"  # Should default to email prefix

        # Empty string name
        request_data = {
            "email": "emptyname@example.com",
            "name": "",
        }

        response = await client.post(
            "/api/v1/auth/verify-google-user", json=request_data
        )

        assert response.status_code == 200
        data = response.json()
        user = data["user"]
        assert user["name"] == "emptyname"  # Should default to email prefix

    async def test_verify_google_user_long_email(self, client: AsyncClient):
        """Test with reasonably long email address."""
        long_email = "a" * 60 + "@verylongdomainname.example.com"  # Reasonable length
        request_data = {
            "email": long_email,
            "name": "Long Email User",
        }

        response = await client.post(
            "/api/v1/auth/verify-google-user", json=request_data
        )

        assert response.status_code == 200
        data = response.json()
        assert data["user"]["email"] == long_email

    async def test_verify_google_user_special_characters(self, client: AsyncClient):
        """Test with special characters in name and image URL."""
        request_data = {
            "email": "special@example.com",
            "name": "José María Ñoño",
            "image": "https://example.com/path/with spaces and unicode 🔥.jpg",
        }

        response = await client.post(
            "/api/v1/auth/verify-google-user", json=request_data
        )

        assert response.status_code == 200
        data = response.json()
        user = data["user"]
        assert user["name"] == "José María Ñoño"
        assert (
            user["image"] == "https://example.com/path/with spaces and unicode 🔥.jpg"
        )

    async def test_verify_google_user_response_schema_validation(
        self, client: AsyncClient
    ):
        """Test that response matches the expected schema exactly."""
        request_data = {
            "email": "schema@example.com",
            "name": "Schema Test",
            "image": "https://example.com/schema.jpg",
            "email_verified": True,
        }

        response = await client.post(
            "/api/v1/auth/verify-google-user", json=request_data
        )

        assert response.status_code == 200
        data = response.json()

        # Validate response can be parsed by our Pydantic model
        try:
            NextAuthVerificationResponse.model_validate(data)
        except Exception as e:
            pytest.fail(f"Response doesn't match schema: {e}")

        # Verify all required fields are present
        assert "user" in data
        assert "tokens" in data

        user = data["user"]
        required_user_fields = ["id", "email", "name", "image"]
        for field in required_user_fields:
            assert field in user

        tokens = data["tokens"]
        required_token_fields = ["access_token", "refresh_token", "expires_in"]
        for field in required_token_fields:
            assert field in tokens

    async def test_nextauth_request_schema_conversion(self):
        """Test NextAuthGoogleUserRequest to GoogleUserInfo conversion."""
        request = NextAuthGoogleUserRequest(
            email="convert@example.com",
            name="Convert Test",
            image="https://example.com/convert.jpg",
            email_verified=True,
        )

        google_info = request.to_google_user_info()

        assert google_info.email == "convert@example.com"
        assert google_info.name == "Convert Test"
        assert (
            google_info.picture == "https://example.com/convert.jpg"
        )  # image -> picture
        assert google_info.email_verified is True
        assert google_info.google_id is None  # Should be None initially

    async def test_verify_google_user_account_linking(
        self, client: AsyncClient, session: AsyncSession
    ):
        """Test that Google ID is properly linked to existing account."""
        # Create user with placeholder Google ID
        from workout_api.users.models import User

        existing_user = User(
            email_address="linking@example.com",
            google_id="temp_placeholder_id",
            name="Existing User",
            is_active=True,
            is_admin=False,
        )
        session.add(existing_user)
        await session.commit()
        await session.refresh(existing_user)

        # Extract user attributes early
        user_id = existing_user.id
        user_email = existing_user.email_address

        request_data = {
            "email": "linking@example.com",
            "name": "Updated Name",
            "image": "https://example.com/linking.jpg",
        }

        response = await client.post(
            "/api/v1/auth/verify-google-user", json=request_data
        )

        assert response.status_code == 200
        data = response.json()

        # Should link to existing user
        user = data["user"]
        assert user["id"] == user_id
        assert user["email"] == user_email
        assert user["name"] == "Updated Name"

    async def test_verify_google_user_content_type_validation(
        self, client: AsyncClient
    ):
        """Test that endpoint requires proper content type."""
        request_data = {
            "email": "content@example.com",
            "name": "Content Test",
        }

        # Test with wrong content type
        response = await client.post(
            "/api/v1/auth/verify-google-user",
            data=str(request_data),  # Not JSON
            headers={"Content-Type": "text/plain"},
        )

        assert response.status_code == 422

        # Test with correct content type
        response = await client.post(
            "/api/v1/auth/verify-google-user",
            json=request_data,
            headers={"Content-Type": "application/json"},
        )

        assert response.status_code == 200
