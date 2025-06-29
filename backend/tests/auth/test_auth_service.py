"""Test auth service with comprehensive coverage."""

from unittest.mock import patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from workout_api.auth.authlib_google import GoogleUserInfo
from workout_api.auth.jwt import JWTManager, TokenPair
from workout_api.auth.service import AuthService
from workout_api.shared.exceptions import (
    AuthenticationError,
    DuplicateError,
    NotFoundError,
)
from workout_api.users.models import User
from workout_api.users.repository import UserRepository

# Mark all tests in this module as anyio tests
pytestmark = pytest.mark.anyio


@pytest.fixture
async def user_repository(session: AsyncSession):
    """Create UserRepository instance with injected session."""
    return UserRepository(session)


@pytest.fixture
async def auth_service(
    session: AsyncSession, jwt_manager: JWTManager, user_repository: UserRepository
):
    """Create AuthService instance with injected dependencies."""
    return AuthService(session, jwt_manager, user_repository)


@pytest.fixture
def alternate_google_user_info() -> GoogleUserInfo:
    """Create alternate Google user info for testing account linking."""
    data = {
        "id": "google_user_456",
        "email": "existing@example.com",
        "name": "Existing User",
        "picture": "https://example.com/existing_avatar.jpg",
        "email_verified": True,
        "given_name": "Existing",
        "family_name": "User",
    }
    return GoogleUserInfo(data)


@pytest.fixture
async def existing_user_no_google(session: AsyncSession):
    """Create a user with different Google ID for account linking tests."""
    user = User(
        email_address="existing@example.com",
        google_id="temp_google_id_to_be_overwritten",  # Will be updated during linking
        name="Existing User",
        is_active=True,
        is_admin=False,
    )
    session.add(user)
    await session.flush()
    await session.refresh(user)
    # Extract attributes early to avoid lazy loading issues
    _ = user.id, user.email_address, user.name, user.is_active
    return user


@pytest.fixture
async def inactive_user(session: AsyncSession):
    """Create an inactive user for testing."""
    user = User(
        email_address="inactive@example.com",
        google_id="google_inactive_789",
        name="Inactive User",
        is_active=False,
        is_admin=False,
    )
    session.add(user)
    await session.flush()
    await session.refresh(user)
    # Extract attributes early
    _ = user.id, user.email_address, user.name, user.is_active
    return user


class TestAuthServiceAuthentication:
    """Test authentication flows in AuthService."""

    async def test_authenticate_with_google_existing_user(
        self,
        auth_service: AuthService,
        test_user: User,
        mock_google_user_info: GoogleUserInfo,
    ):
        """Test authentication with existing user by Google ID."""
        # Extract user attributes early to avoid lazy loading issues
        user_id = test_user.id
        user_email = test_user.email_address
        user_name = test_user.name

        # Act
        user, tokens = await auth_service.authenticate_with_google(
            mock_google_user_info
        )

        # Assert
        assert user.id == user_id
        assert user.email_address == user_email
        assert user.name == user_name
        assert isinstance(tokens, TokenPair)
        assert tokens.access_token is not None
        assert tokens.refresh_token is not None

    async def test_authenticate_with_google_account_linking(
        self,
        auth_service: AuthService,
        existing_user_no_google: User,
        alternate_google_user_info: GoogleUserInfo,
    ):
        """Test linking Google account to existing user by email."""
        # Extract attributes early
        user_id = existing_user_no_google.id
        user_email = existing_user_no_google.email_address

        # Act
        user, tokens = await auth_service.authenticate_with_google(
            alternate_google_user_info
        )

        # Assert
        assert user.id == user_id
        assert user.email_address == user_email
        assert user.google_id == "google_user_456"
        assert user.name == "Existing User"  # Updated from Google info
        assert isinstance(tokens, TokenPair)

    async def test_authenticate_with_google_new_user(
        self, auth_service: AuthService, mock_google_user_info: GoogleUserInfo
    ):
        """Test creating new user from Google OAuth."""
        # Act
        user, tokens = await auth_service.authenticate_with_google(
            mock_google_user_info
        )

        # Assert
        assert user.id is not None
        assert user.email_address == "test@example.com"
        assert user.name == "Test User"
        assert user.google_id == "google_user_123"
        assert user.is_active is True
        assert user.is_admin is False
        assert isinstance(tokens, TokenPair)

    async def test_authenticate_with_google_user_info_update(
        self, auth_service: AuthService, test_user: User
    ):
        """Test updating existing user info during authentication."""
        # Create Google user info with updated details
        google_info_data = {
            "id": "google_user_123",  # Same as test_user
            "email": "test@example.com",
            "name": "Updated Name",
            "picture": "https://example.com/new_avatar.jpg",
            "email_verified": True,
        }
        google_info = GoogleUserInfo(google_info_data)

        # Extract original user attributes
        user_id = test_user.id
        user_email = test_user.email_address

        # Act
        user, tokens = await auth_service.authenticate_with_google(google_info)

        # Assert
        assert user.id == user_id
        assert user.email_address == user_email
        assert user.name == "Updated Name"  # Updated
        assert (
            str(user.profile_image_url) == "https://example.com/new_avatar.jpg"
        )  # Updated
        isinstance(tokens, TokenPair)

    async def test_authenticate_with_google_database_error(
        self, auth_service: AuthService, mock_google_user_info: GoogleUserInfo
    ):
        """Test authentication with database error causes rollback."""
        # Mock the user repository to raise an exception
        with (
            patch.object(
                auth_service.user_repository,
                "get_by_google_id",
                side_effect=Exception("DB Error"),
            ),
            pytest.raises(AuthenticationError, match="Authentication failed: DB Error"),
        ):
            await auth_service.authenticate_with_google(mock_google_user_info)

    async def test_authenticate_with_google_jwt_error(
        self,
        auth_service: AuthService,
        test_user: User,  # noqa: ARG002
        mock_google_user_info: GoogleUserInfo,
    ):
        """Test authentication with JWT creation error."""
        # Mock JWT manager to raise an exception
        with (
            patch.object(
                auth_service.jwt_manager,
                "create_token_pair",
                side_effect=Exception("JWT Error"),
            ),
            pytest.raises(
                AuthenticationError, match="Authentication failed: JWT Error"
            ),
        ):
            await auth_service.authenticate_with_google(mock_google_user_info)


class TestAuthServiceTokenManagement:
    """Test token management in AuthService."""

    async def test_refresh_user_token_success(
        self, auth_service: AuthService, test_user: User
    ):
        """Test successful token refresh."""
        # Extract user attributes early
        user_id = test_user.id

        # Act
        tokens = await auth_service.refresh_user_token(user_id)

        # Assert
        assert isinstance(tokens, TokenPair)
        assert tokens.access_token is not None
        assert tokens.refresh_token is not None

    async def test_refresh_user_token_user_not_found(self, auth_service: AuthService):
        """Test token refresh for non-existent user."""
        # Act & Assert
        with pytest.raises(NotFoundError, match="User not found"):
            await auth_service.refresh_user_token(999)

    async def test_refresh_user_token_inactive_user(
        self, auth_service: AuthService, inactive_user: User
    ):
        """Test token refresh for inactive user."""
        # Extract user ID early
        user_id = inactive_user.id

        # Act & Assert
        with pytest.raises(AuthenticationError, match="User account is inactive"):
            await auth_service.refresh_user_token(user_id)

    async def test_refresh_user_token_jwt_error(
        self, auth_service: AuthService, test_user: User
    ):
        """Test token refresh with JWT creation error."""
        # Extract user ID early
        user_id = test_user.id

        # Mock JWT manager to raise an exception
        with (
            patch.object(
                auth_service.jwt_manager,
                "create_token_pair",
                side_effect=Exception("JWT Error"),
            ),
            pytest.raises(AuthenticationError, match="Token refresh failed"),
        ):
            await auth_service.refresh_user_token(user_id)


class TestAuthServiceUserManagement:
    """Test user management operations in AuthService."""

    async def test_deactivate_user_success(
        self, auth_service: AuthService, test_user: User
    ):
        """Test successful user deactivation."""
        # Extract user ID early
        user_id = test_user.id

        # Act
        result = await auth_service.deactivate_user(user_id)

        # Assert
        assert result is True

    async def test_deactivate_user_not_found(self, auth_service: AuthService):
        """Test user deactivation for non-existent user."""
        # Act & Assert
        with pytest.raises(NotFoundError, match="User not found"):
            await auth_service.deactivate_user(999)

    async def test_deactivate_user_database_error(
        self, auth_service: AuthService, test_user: User
    ):
        """Test user deactivation with database error causes rollback."""
        # Extract user ID early
        user_id = test_user.id

        # Mock repository to raise an exception
        with (
            patch.object(
                auth_service.user_repository,
                "soft_delete",
                side_effect=Exception("DB Error"),
            ),
            pytest.raises(AuthenticationError, match="Failed to deactivate user"),
        ):
            await auth_service.deactivate_user(user_id)

    async def test_get_user_profile_success(
        self, auth_service: AuthService, test_user: User
    ):
        """Test successful user profile retrieval."""
        # Extract user attributes early
        user_id = test_user.id
        user_email = test_user.email_address
        user_name = test_user.name

        # Act
        user = await auth_service.get_user_profile(user_id)

        # Assert
        assert user.id == user_id
        assert user.email_address == user_email
        assert user.name == user_name

    async def test_get_user_profile_not_found(self, auth_service: AuthService):
        """Test user profile retrieval for non-existent user."""
        # Act & Assert
        with pytest.raises(NotFoundError, match="User not found"):
            await auth_service.get_user_profile(999)

    async def test_get_user_profile_database_error(
        self, auth_service: AuthService, test_user: User
    ):
        """Test user profile retrieval with database error."""
        # Extract user ID early
        user_id = test_user.id

        # Mock repository to raise an exception
        with (
            patch.object(
                auth_service.user_repository,
                "get_by_id",
                side_effect=Exception("DB Error"),
            ),
            pytest.raises(AuthenticationError, match="Failed to retrieve user profile"),
        ):
            await auth_service.get_user_profile(user_id)

    async def test_update_user_profile_success(
        self, auth_service: AuthService, test_user: User
    ):
        """Test successful user profile update."""
        # Extract user attributes early
        user_id = test_user.id
        user_email = test_user.email_address

        # Prepare update data
        update_data = {
            "name": "Updated Name",
            "profile_image_url": "https://example.com/new_avatar.jpg",
            "email_address": "should_not_update@example.com",  # Should be filtered out
        }

        # Act
        updated_user = await auth_service.update_user_profile(user_id, update_data)

        # Assert
        assert updated_user is not None
        # Extract attributes immediately after the service call
        updated_user_email = updated_user.email_address
        assert updated_user_email == user_email  # Should not change
        # Note: We avoid accessing lazy-loaded attributes after transaction boundaries

    async def test_update_user_profile_not_found(self, auth_service: AuthService):
        """Test user profile update for non-existent user."""
        # Prepare update data
        update_data = {"name": "New Name"}

        # Act & Assert
        with pytest.raises(NotFoundError, match="User not found"):
            await auth_service.update_user_profile(999, update_data)

    async def test_update_user_profile_database_error(
        self, auth_service: AuthService, test_user: User
    ):
        """Test user profile update with database error causes rollback."""
        # Extract user ID early
        user_id = test_user.id

        # Prepare update data
        update_data = {"name": "New Name"}

        # Mock repository to raise an exception
        with (
            patch.object(
                auth_service.user_repository,
                "update",
                side_effect=Exception("DB Error"),
            ),
            pytest.raises(AuthenticationError, match="Failed to update user profile"),
        ):
            await auth_service.update_user_profile(user_id, update_data)

    async def test_validate_user_access_active_user(
        self, auth_service: AuthService, test_user: User
    ):
        """Test access validation for active user."""
        # Extract user ID early
        user_id = test_user.id

        # Act
        result = await auth_service.validate_user_access(user_id)

        # Assert
        assert result is True

    async def test_validate_user_access_inactive_user(
        self, auth_service: AuthService, inactive_user: User
    ):
        """Test access validation for inactive user."""
        # Extract user ID early
        user_id = inactive_user.id

        # Act
        result = await auth_service.validate_user_access(user_id)

        # Assert
        assert result is False

    async def test_validate_user_access_user_not_found(self, auth_service: AuthService):
        """Test access validation for non-existent user."""
        # Act
        result = await auth_service.validate_user_access(999)

        # Assert
        assert result is False

    async def test_validate_user_access_database_error(
        self, auth_service: AuthService, test_user: User
    ):
        """Test access validation with database error."""
        # Extract user ID early
        user_id = test_user.id

        # Mock repository to raise an exception
        with patch.object(
            auth_service.user_repository, "get_by_id", side_effect=Exception("DB Error")
        ):
            # Act
            result = await auth_service.validate_user_access(user_id)

            # Assert - Should return False on error
            assert result is False


class TestAuthServicePrivateMethods:
    """Test private methods of AuthService."""

    async def test_create_user_from_google_success(self, auth_service: AuthService):
        """Test successful user creation from Google info."""
        # Create Google user info
        google_info_data = {
            "id": "new_google_user_999",
            "email": "newuser@example.com",
            "name": "New User",
            "picture": "https://example.com/new_user_avatar.jpg",
            "email_verified": True,
        }
        google_info = GoogleUserInfo(google_info_data)

        # Act
        user = await auth_service._create_user_from_google(google_info)

        # Assert - Extract all attributes immediately to avoid lazy loading
        user_id = user.id
        user_email = user.email_address
        user_name = user.name
        user_google_id = user.google_id
        user_profile_image_url = str(user.profile_image_url)
        user_is_active = user.is_active
        user_is_admin = user.is_admin

        assert user_id is not None
        assert user_email == "newuser@example.com"
        assert user_name == "New User"
        assert user_google_id == "new_google_user_999"
        assert user_profile_image_url == "https://example.com/new_user_avatar.jpg"
        assert user_is_active is True
        assert user_is_admin is False

    async def test_create_user_from_google_no_name(self, auth_service: AuthService):
        """Test user creation from Google info without name (uses email prefix)."""
        # Create Google user info without name
        google_info_data = {
            "id": "no_name_user_888",
            "email": "noname@example.com",
            "email_verified": True,
        }
        google_info = GoogleUserInfo(google_info_data)

        # Act
        user = await auth_service._create_user_from_google(google_info)

        # Assert - Extract attributes immediately to avoid lazy loading
        user_name = user.name
        assert user_name == "noname"  # Should use email prefix

    async def test_create_user_from_google_database_error(
        self, auth_service: AuthService
    ):
        """Test user creation with database error causes rollback."""
        # Create Google user info
        google_info_data = {
            "id": "error_user_777",
            "email": "error@example.com",
            "name": "Error User",
            "email_verified": True,
        }
        google_info = GoogleUserInfo(google_info_data)

        # Mock repository to raise an exception
        with (
            patch.object(
                auth_service.user_repository,
                "create",
                side_effect=Exception("DB Error"),
            ),
            pytest.raises(
                DuplicateError, match="User already exists or creation failed"
            ),
        ):
            await auth_service._create_user_from_google(google_info)

    async def test_update_user_from_google_with_changes(
        self, auth_service: AuthService, test_user: User
    ):
        """Test updating user from Google info with changes."""
        # Extract user attributes early
        user_id = test_user.id
        user_email = test_user.email_address

        # Create Google user info with updates
        google_info_data = {
            "id": "google_user_123",
            "email": "test@example.com",
            "name": "Updated Name",
            "picture": "https://example.com/updated_avatar.jpg",
            "email_verified": True,
        }
        google_info = GoogleUserInfo(google_info_data)

        # Act
        updated_user = await auth_service._update_user_from_google(
            test_user, google_info
        )

        # Assert
        assert updated_user.id == user_id
        assert updated_user.email_address == user_email
        assert updated_user.name == "Updated Name"
        assert (
            str(updated_user.profile_image_url)
            == "https://example.com/updated_avatar.jpg"
        )

    async def test_update_user_from_google_no_changes(
        self, auth_service: AuthService, test_user: User
    ):
        """Test updating user from Google info with no changes."""
        # Extract user attributes early
        user_id = test_user.id
        user_name = test_user.name

        # Create Google user info with same data
        google_info_data = {
            "id": "google_user_123",
            "email": "test@example.com",
            "name": user_name,  # Same name
            "picture": str(test_user.profile_image_url),  # Same picture
            "email_verified": True,
        }
        google_info = GoogleUserInfo(google_info_data)

        # Act
        updated_user = await auth_service._update_user_from_google(
            test_user, google_info
        )

        # Assert - Should return same user without database changes
        assert updated_user.id == user_id
        assert updated_user.name == user_name

    async def test_update_user_from_google_activate_user(
        self, auth_service: AuthService, inactive_user: User
    ):
        """Test updating inactive user from Google info activates them."""
        # Extract user attributes early
        user_id = inactive_user.id

        # Create Google user info
        google_info_data = {
            "id": "google_inactive_789",
            "email": "inactive@example.com",
            "name": "Inactive User",
            "email_verified": True,
        }
        google_info = GoogleUserInfo(google_info_data)

        # Act
        updated_user = await auth_service._update_user_from_google(
            inactive_user, google_info
        )

        # Assert
        assert updated_user.id == user_id
        assert updated_user.is_active is True  # Should be activated

    async def test_update_user_from_google_database_error(
        self, auth_service: AuthService, test_user: User
    ):
        """Test updating user from Google info with database error causes rollback."""
        # Create Google user info with updates
        google_info_data = {
            "id": "google_user_123",
            "email": "test@example.com",
            "name": "Updated Name",
            "email_verified": True,
        }
        google_info = GoogleUserInfo(google_info_data)

        # Mock session commit to raise an exception
        with (
            patch.object(
                auth_service.session, "commit", side_effect=Exception("DB Error")
            ),
            pytest.raises(
                AuthenticationError, match="Failed to update user information"
            ),
        ):
            await auth_service._update_user_from_google(test_user, google_info)


class TestAuthServiceExceptionHandling:
    """Test exception handling and logging in AuthService."""

    async def test_exception_chaining_authentication_error(
        self, auth_service: AuthService, mock_google_user_info: GoogleUserInfo
    ):
        """Test that exceptions are properly chained with 'from e'."""
        # Mock to raise a specific exception
        original_exception = Exception("Original error")
        with patch.object(
            auth_service.user_repository,
            "get_by_google_id",
            side_effect=original_exception,
        ):
            # Act & Assert
            with pytest.raises(AuthenticationError) as exc_info:
                await auth_service.authenticate_with_google(mock_google_user_info)

            # Verify exception chaining
            assert exc_info.value.__cause__ is original_exception

    async def test_logging_on_errors(
        self, auth_service: AuthService, mock_google_user_info: GoogleUserInfo
    ):
        """Test that errors are properly logged."""
        with (
            patch("workout_api.auth.service.logger") as mock_logger,
            patch.object(
                auth_service.user_repository,
                "get_by_google_id",
                side_effect=Exception("Test error"),
            ),
        ):
            # Act
            with pytest.raises(AuthenticationError):
                await auth_service.authenticate_with_google(mock_google_user_info)

            # Assert
            mock_logger.error.assert_called_once()

    async def test_session_rollback_on_errors(
        self, auth_service: AuthService, mock_google_user_info: GoogleUserInfo
    ):
        """Test that session rollback is called on errors."""
        with (
            patch.object(auth_service.session, "rollback") as mock_rollback,
            patch.object(
                auth_service.user_repository,
                "get_by_google_id",
                side_effect=Exception("Test error"),
            ),
        ):
            # Act
            with pytest.raises(AuthenticationError):
                await auth_service.authenticate_with_google(mock_google_user_info)

            # Assert
            mock_rollback.assert_called_once()
