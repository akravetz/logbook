"""Test auth service with comprehensive coverage."""

from unittest.mock import AsyncMock, Mock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from workout_api.auth.google_verification import GoogleTokenInfo, GoogleTokenVerifier
from workout_api.auth.jwt import JWTManager
from workout_api.auth.service import AuthService
from workout_api.shared.exceptions import AuthenticationError, NotFoundError
from workout_api.users.repository import UserRepository

# Mark all tests in this module as anyio tests
pytestmark = pytest.mark.anyio


@pytest.fixture
def mock_google_verifier():
    """Create mock Google token verifier."""
    mock = Mock(spec=GoogleTokenVerifier)
    mock.verify_access_token = AsyncMock()
    return mock


@pytest.fixture
def auth_service(
    session: AsyncSession,
    jwt_manager: JWTManager,
    user_repository: UserRepository,
    mock_google_verifier: GoogleTokenVerifier,
):
    """Create AuthService with real repository for integration testing."""
    return AuthService(
        session=session,
        jwt_manager=jwt_manager,
        user_repository=user_repository,
        google_verifier=mock_google_verifier,
    )


@pytest.fixture
def sample_google_token_info():
    """Create sample Google token info."""
    return GoogleTokenInfo(
        email="test@example.com",
        name="Test User",
        picture="https://example.com/avatar.jpg",
        user_id="google_123",
        email_verified=True,
        audience="test_client_id",
        expires_in=3600,
    )


class TestAuthServiceAuthentication:
    """Test main authentication method."""

    async def test_authenticate_with_verified_google_token_new_user(
        self,
        auth_service: AuthService,
        session: AsyncSession,  # noqa: ARG002
        user_repository: UserRepository,
        mock_google_verifier: GoogleTokenVerifier,
        sample_google_token_info: GoogleTokenInfo,
    ):
        """Test authentication with verified token for new user."""
        # Arrange
        access_token = "valid_google_token"
        mock_google_verifier.verify_access_token.return_value = sample_google_token_info

        # Verify no existing user
        existing_user = await user_repository.get_by_email("test@example.com")
        assert existing_user is None

        # Act
        (
            user,
            session_token,
        ) = await auth_service.authenticate_with_verified_google_token(access_token)

        # Assert
        assert user is not None
        assert user.email_address == "test@example.com"
        assert user.google_id == "google_123"
        assert user.name == "Test User"
        assert user.profile_image_url == "https://example.com/avatar.jpg"
        assert user.is_active is True
        assert user.is_admin is False
        assert user.id is not None
        assert isinstance(session_token, str)
        assert len(session_token) > 0

        # Verify Google verifier was called
        mock_google_verifier.verify_access_token.assert_called_once_with(access_token)

        # Verify user was created in database
        created_user = await user_repository.get_by_email("test@example.com")
        assert created_user is not None
        assert created_user.id == user.id
        assert created_user.google_id == "google_123"

    async def test_authenticate_with_verified_google_token_existing_user(
        self,
        auth_service: AuthService,
        session: AsyncSession,  # noqa: ARG002
        user_repository: UserRepository,
        mock_google_verifier: GoogleTokenVerifier,
        sample_google_token_info: GoogleTokenInfo,
    ):
        """Test authentication with verified token for existing user."""
        # Arrange
        access_token = "valid_google_token"
        mock_google_verifier.verify_access_token.return_value = sample_google_token_info

        # Create existing user with different data that should be updated
        existing_user_data = {
            "email_address": "test@example.com",
            "google_id": "old_google_id",  # Different from token
            "name": "Existing User",  # Different from token
            "profile_image_url": "https://example.com/old_avatar.jpg",  # Different from token
            "is_active": True,
            "is_admin": False,
        }
        existing_user = await user_repository.create(existing_user_data)
        existing_user_id = existing_user.id

        # Act
        (
            user,
            session_token,
        ) = await auth_service.authenticate_with_verified_google_token(access_token)

        # Assert
        assert user is not None
        assert user.id == existing_user_id
        assert user.email_address == "test@example.com"
        assert user.google_id == "google_123"  # Updated from token
        assert user.name == "Test User"  # Updated from token
        assert (
            user.profile_image_url == "https://example.com/avatar.jpg"
        )  # Updated from token
        assert user.is_active is True
        assert user.is_admin is False
        assert isinstance(session_token, str)
        assert len(session_token) > 0

        # Verify Google verifier was called
        mock_google_verifier.verify_access_token.assert_called_once_with(access_token)

        # Verify user was updated in database
        updated_user = await user_repository.get_by_email("test@example.com")
        assert updated_user is not None
        assert updated_user.id == existing_user_id
        assert updated_user.google_id == "google_123"
        assert updated_user.name == "Test User"
        assert updated_user.profile_image_url == "https://example.com/avatar.jpg"

    async def test_authenticate_with_verified_google_token_no_verifier(
        self,
        session: AsyncSession,
        jwt_manager: JWTManager,
        user_repository: UserRepository,
    ):
        """Test authentication fails when Google verifier is not configured."""
        # Arrange
        auth_service = AuthService(
            session=session,
            jwt_manager=jwt_manager,
            user_repository=user_repository,
            google_verifier=None,  # No verifier
        )

        # Act & Assert
        with pytest.raises(
            AuthenticationError, match="Google token verification not configured"
        ):
            await auth_service.authenticate_with_verified_google_token("token")

    async def test_authenticate_with_verified_google_token_verification_fails(
        self,
        auth_service: AuthService,
        mock_google_verifier: GoogleTokenVerifier,
    ):
        """Test authentication fails when Google token verification fails."""
        # Arrange
        access_token = "invalid_google_token"
        mock_google_verifier.verify_access_token.side_effect = AuthenticationError(
            "Invalid token"
        )

        # Act & Assert
        with pytest.raises(AuthenticationError, match="Invalid token"):
            await auth_service.authenticate_with_verified_google_token(access_token)

    async def test_authenticate_with_verified_google_token_unexpected_error(
        self,
        auth_service: AuthService,
        user_repository: UserRepository,
        mock_google_verifier: GoogleTokenVerifier,
        sample_google_token_info: GoogleTokenInfo,
    ):
        """Test authentication handles unexpected errors gracefully."""
        # Arrange
        access_token = "valid_google_token"
        mock_google_verifier.verify_access_token.return_value = sample_google_token_info

        # Patch the repository to raise an exception
        with (
            patch.object(
                user_repository, "get_by_email", side_effect=Exception("Database error")
            ),
            pytest.raises(
                AuthenticationError, match="Verified Google authentication failed"
            ),
        ):
            await auth_service.authenticate_with_verified_google_token(access_token)


class TestAuthServiceUserCreation:
    """Test user creation from Google token."""

    async def test_create_user_from_verified_google_success(
        self,
        auth_service: AuthService,
        session: AsyncSession,  # noqa: ARG002
        user_repository: UserRepository,
        sample_google_token_info: GoogleTokenInfo,
    ):
        """Test successful user creation from verified Google token."""
        # Arrange - verify no existing user
        existing_user = await user_repository.get_by_email("test@example.com")
        assert existing_user is None

        # Act
        result = await auth_service._create_user_from_verified_google(
            sample_google_token_info
        )

        # Assert
        assert result is not None
        assert result.email_address == "test@example.com"
        assert result.google_id == "google_123"
        assert result.name == "Test User"
        assert result.profile_image_url == "https://example.com/avatar.jpg"
        assert result.is_active is True
        assert result.is_admin is False
        assert result.id is not None

        # Verify user was created in database
        created_user = await user_repository.get_by_email("test@example.com")
        assert created_user is not None
        assert created_user.id == result.id
        assert created_user.google_id == "google_123"

    async def test_create_user_from_verified_google_no_name(
        self,
        auth_service: AuthService,
        session: AsyncSession,  # noqa: ARG002
        user_repository: UserRepository,
    ):
        """Test user creation when Google token has no name."""
        # Arrange
        token_info = GoogleTokenInfo(
            email="test@example.com",
            name=None,  # No name provided
            picture="https://example.com/avatar.jpg",
            user_id="google_123",
            email_verified=True,
            audience="test_client_id",
            expires_in=3600,
        )

        # Verify no existing user
        existing_user = await user_repository.get_by_email("test@example.com")
        assert existing_user is None

        # Act
        result = await auth_service._create_user_from_verified_google(token_info)

        # Assert
        assert result is not None
        assert result.email_address == "test@example.com"
        assert result.google_id == "google_123"
        assert result.name == "test"  # Derived from email prefix
        assert result.profile_image_url == "https://example.com/avatar.jpg"
        assert result.is_active is True
        assert result.is_admin is False
        assert result.id is not None

        # Verify user was created in database
        created_user = await user_repository.get_by_email("test@example.com")
        assert created_user is not None
        assert created_user.id == result.id
        assert created_user.name == "test"

    async def test_create_user_from_verified_google_repository_error(
        self,
        auth_service: AuthService,
        user_repository: UserRepository,
        sample_google_token_info: GoogleTokenInfo,
    ):
        """Test user creation handles repository errors."""
        # Arrange - patch the repository create method to raise an exception
        with (
            patch.object(
                user_repository, "create", side_effect=Exception("Database error")
            ),
            pytest.raises(AuthenticationError, match="Failed to create user account"),
        ):
            await auth_service._create_user_from_verified_google(
                sample_google_token_info
            )


class TestAuthServiceUserUpdate:
    """Test user update from Google token."""

    async def test_update_user_from_verified_google_with_changes(
        self,
        auth_service: AuthService,
        session: AsyncSession,  # noqa: ARG002
        user_repository: UserRepository,
        sample_google_token_info: GoogleTokenInfo,
    ):
        """Test user update when there are changes to apply."""
        # Arrange - create existing user with different data than token
        existing_user_data = {
            "email_address": "test@example.com",
            "google_id": "old_google_id",  # Different from token
            "name": "Old Name",  # Different from token
            "profile_image_url": "https://example.com/old.jpg",  # Different from token
            "is_active": True,
            "is_admin": False,
        }
        existing_user = await user_repository.create(existing_user_data)
        existing_user_id = existing_user.id

        # Act
        result = await auth_service._update_user_from_verified_google(
            existing_user, sample_google_token_info
        )

        # Assert
        assert result is not None
        assert result.id == existing_user_id
        assert result.email_address == "test@example.com"
        assert result.google_id == "google_123"  # Updated
        assert result.name == "Test User"  # Updated
        assert result.profile_image_url == "https://example.com/avatar.jpg"  # Updated
        assert result.is_active is True
        assert result.is_admin is False

        # Verify user was updated in database
        updated_user = await user_repository.get_by_id(existing_user_id)
        assert updated_user is not None
        assert updated_user.google_id == "google_123"
        assert updated_user.name == "Test User"
        assert updated_user.profile_image_url == "https://example.com/avatar.jpg"

    async def test_update_user_from_verified_google_no_changes(
        self,
        auth_service: AuthService,
        session: AsyncSession,  # noqa: ARG002
        user_repository: UserRepository,
        sample_google_token_info: GoogleTokenInfo,
    ):
        """Test user update when no changes are needed."""
        # Arrange - create user with same data as token
        existing_user_data = {
            "email_address": "test@example.com",
            "google_id": "google_123",  # Same as token
            "name": "Test User",  # Same as token
            "profile_image_url": "https://example.com/avatar.jpg",  # Same as token
            "is_active": True,
            "is_admin": False,
        }
        existing_user = await user_repository.create(existing_user_data)
        existing_user_id = existing_user.id
        original_updated_at = existing_user.updated_at

        # Act
        result = await auth_service._update_user_from_verified_google(
            existing_user, sample_google_token_info
        )

        # Assert
        assert result is not None
        assert result.id == existing_user_id
        assert result.email_address == "test@example.com"
        assert result.google_id == "google_123"
        assert result.name == "Test User"
        assert result.profile_image_url == "https://example.com/avatar.jpg"

        # Verify no changes in database (updated_at should be the same)
        unchanged_user = await user_repository.get_by_id(existing_user_id)
        assert unchanged_user.updated_at == original_updated_at

    async def test_update_user_from_verified_google_partial_changes(
        self,
        auth_service: AuthService,
        session: AsyncSession,  # noqa: ARG002
        user_repository: UserRepository,
    ):
        """Test user update with only some fields changed."""
        # Arrange
        token_info = GoogleTokenInfo(
            email="test@example.com",
            name="New Name",  # Different
            picture="https://example.com/avatar.jpg",  # Same
            user_id="google_123",  # Same
            email_verified=True,
            audience="test_client_id",
            expires_in=3600,
        )

        # Create existing user with some same and some different data
        existing_user_data = {
            "email_address": "test@example.com",
            "google_id": "google_123",  # Same as token
            "name": "Old Name",  # Different from token
            "profile_image_url": "https://example.com/avatar.jpg",  # Same as token
            "is_active": True,
            "is_admin": False,
        }
        existing_user = await user_repository.create(existing_user_data)
        existing_user_id = existing_user.id

        # Act
        result = await auth_service._update_user_from_verified_google(
            existing_user, token_info
        )

        # Assert
        assert result is not None
        assert result.id == existing_user_id
        assert result.email_address == "test@example.com"
        assert result.google_id == "google_123"  # Same
        assert result.name == "New Name"  # Updated
        assert result.profile_image_url == "https://example.com/avatar.jpg"  # Same
        assert result.is_active is True
        assert result.is_admin is False

        # Verify only name was updated in database
        updated_user = await user_repository.get_by_id(existing_user_id)
        assert updated_user is not None
        assert updated_user.name == "New Name"
        assert updated_user.google_id == "google_123"  # Unchanged
        assert (
            updated_user.profile_image_url == "https://example.com/avatar.jpg"
        )  # Unchanged

    async def test_update_user_from_verified_google_repository_error(
        self,
        auth_service: AuthService,
        user_repository: UserRepository,
        sample_google_token_info: GoogleTokenInfo,
    ):
        """Test user update handles repository errors."""
        # Arrange - create existing user that needs updates
        existing_user_data = {
            "email_address": "test@example.com",
            "google_id": "old_google_id",
            "name": "Old Name",  # Different from token
            "is_active": True,
            "is_admin": False,
        }
        existing_user = await user_repository.create(existing_user_data)

        # Patch the repository update method to raise an exception
        with (
            patch.object(
                user_repository, "update", side_effect=Exception("Database error")
            ),
            pytest.raises(
                AuthenticationError, match="Failed to update user information"
            ),
        ):
            await auth_service._update_user_from_verified_google(
                existing_user, sample_google_token_info
            )

    async def test_update_user_from_verified_google_not_found_error(
        self,
        auth_service: AuthService,
        user_repository: UserRepository,
        sample_google_token_info: GoogleTokenInfo,
    ):
        """Test user update handles NotFoundError properly."""
        # Arrange - create existing user that needs updates
        existing_user_data = {
            "email_address": "test@example.com",
            "google_id": "old_google_id",
            "name": "Old Name",  # Different from token
            "is_active": True,
            "is_admin": False,
        }
        existing_user = await user_repository.create(existing_user_data)

        # Patch the repository update method to raise NotFoundError
        with (
            patch.object(
                user_repository, "update", side_effect=NotFoundError("User not found")
            ),
            pytest.raises(NotFoundError, match="User not found"),
        ):
            await auth_service._update_user_from_verified_google(
                existing_user, sample_google_token_info
            )
