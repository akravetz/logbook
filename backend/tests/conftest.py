"""Test configuration with anyio and transaction isolation."""

from collections.abc import AsyncGenerator
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from testcontainers.postgres import PostgresContainer

from workout_api.auth.dependencies import get_current_user_from_token
from workout_api.auth.jwt import JWTManager, TokenPair
from workout_api.core.config import Settings
from workout_api.core.database import get_session
from workout_api.core.main import app
from workout_api.shared.base_model import Base
from workout_api.users.models import User
from workout_api.users.repository import UserRepository

# Mark all tests in this session as anyio tests
pytestmark = pytest.mark.anyio


# Define session-scoped anyio_backend for higher-scoped async fixtures
@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest.fixture(scope="session")
def postgres_container():
    """Start PostgreSQL container for entire test session."""
    with PostgresContainer("postgres:16", driver="asyncpg") as postgres:
        yield postgres


@pytest.fixture(scope="session")
async def test_engine(postgres_container, anyio_backend):  # noqa: ARG001
    """Create test database engine with session scope."""
    database_url = postgres_container.get_connection_url()

    engine = create_async_engine(
        database_url,
        echo=False,  # Set to True for SQL debugging
    )

    # Create all tables once per session
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Cleanup
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
    finally:
        await engine.dispose()


@pytest.fixture
async def session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create test session with transaction isolation."""
    async with test_engine.connect() as connection:
        # Begin external transaction
        trans = await connection.begin()

        # Create session with savepoint mode for transaction isolation
        session = AsyncSession(
            bind=connection, join_transaction_mode="create_savepoint"
        )

        try:
            yield session
        finally:
            await session.close()
            # Rollback the external transaction - undoes all changes
            await trans.rollback()


@pytest.fixture
async def client(session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create async test client with database dependency override."""

    async def override_get_session():
        yield session

    app.dependency_overrides[get_session] = override_get_session

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            yield ac
    finally:
        # Clean up dependency overrides
        app.dependency_overrides.clear()


# ================================
# Common Application Fixtures
# ================================


@pytest.fixture
def test_settings() -> Settings:
    """Create test settings - shared across all modules."""
    return Settings(
        jwt_secret_key="test_secret_key_12345678901234567890",  # gitleaks:allow
        jwt_algorithm="HS256",
        access_token_expire_minutes=30,
        refresh_token_expire_days=7,
        database_url="postgresql://test:test@localhost/test",
        google_client_id="test_client_id",
        deepgram_api_key="test_deepgram_key",  # gitleaks:allow
    )


@pytest.fixture
def jwt_manager(test_settings: Settings) -> JWTManager:
    """Create JWT manager for testing - shared across modules."""
    return JWTManager(test_settings)


# ================================
# User-related Common Fixtures
# ================================


@pytest.fixture
def test_user_data() -> dict[str, Any]:
    """Standard test user data - shared across modules."""
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
    """Standard test admin user data - shared across modules."""
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
def another_user_data() -> dict[str, Any]:
    """Standard second user data for testing interactions - shared across modules."""
    return {
        "id": 3,
        "email_address": "another@example.com",
        "google_id": "google_another_789",
        "name": "Another User",
        "profile_image_url": "https://example.com/another_avatar.jpg",
        "is_active": True,
        "is_admin": False,
    }


async def _create_user_from_data(
    session: AsyncSession, user_data: dict[str, Any]
) -> User:
    """Helper function to create a user and extract attributes to prevent lazy loading."""
    user = User(**user_data)
    session.add(user)
    await session.flush()  # Get the ID without committing
    await session.refresh(user)

    # Extract all attributes early to prevent MissingGreenlet errors
    _ = (
        user.id,
        user.email_address,
        user.google_id,
        user.name,
        user.profile_image_url,
        user.is_active,
        user.is_admin,
        user.created_at,
        user.updated_at,
    )

    return user


@pytest.fixture
async def test_user(session: AsyncSession, test_user_data: dict[str, Any]) -> User:
    """Create standard test user in database - shared across modules."""
    return await _create_user_from_data(session, test_user_data)


@pytest.fixture
async def test_admin_user(
    session: AsyncSession, test_admin_user_data: dict[str, Any]
) -> User:
    """Create standard admin user in database - shared across modules."""
    return await _create_user_from_data(session, test_admin_user_data)


@pytest.fixture
async def another_user(
    session: AsyncSession, another_user_data: dict[str, Any]
) -> User:
    """Create second user for interaction testing - shared across modules."""
    return await _create_user_from_data(session, another_user_data)


@pytest.fixture
async def inactive_user(session: AsyncSession) -> User:
    """Create inactive user for testing - shared across modules."""
    user_data = {
        "email_address": "inactive@example.com",
        "google_id": "google_inactive_999",
        "name": "Inactive User",
        "is_active": False,
        "is_admin": False,
    }
    return await _create_user_from_data(session, user_data)


# ================================
# Auth-related Common Fixtures
# ================================


@pytest.fixture
def valid_token_pair(
    test_user_data: dict[str, Any], jwt_manager: JWTManager
) -> TokenPair:
    """Create valid JWT token pair for testing - shared across modules."""
    return jwt_manager.create_token_pair(
        test_user_data["id"], test_user_data["email_address"]
    )


# ================================
# HTTP Client Fixtures with Authentication
# ================================


@pytest.fixture
async def authenticated_client(
    client: AsyncClient, test_user: User, session: AsyncSession
) -> AsyncClient:
    """Create authenticated HTTP client for standard user - shared across modules."""
    # Extract user_id early to avoid lazy loading issues
    user_id = test_user.id

    async def override_get_current_user_from_token():
        # Get a fresh user object from the database for each request to avoid detached instance issues
        stmt = select(User).where(User.id == user_id)
        result = await session.execute(stmt)
        fresh_user = result.scalar_one()
        return fresh_user

    app.dependency_overrides[get_current_user_from_token] = (
        override_get_current_user_from_token
    )
    yield client

    # Clean up this specific override (client fixture cleans up get_session)
    if get_current_user_from_token in app.dependency_overrides:
        del app.dependency_overrides[get_current_user_from_token]


@pytest.fixture
async def admin_authenticated_client(
    client: AsyncClient, test_admin_user: User, session: AsyncSession
) -> AsyncClient:
    """Create authenticated HTTP client for admin user - shared across modules."""
    # Extract user_id early to avoid lazy loading issues
    user_id = test_admin_user.id

    async def override_get_current_user_from_token():
        # Get a fresh user object from the database for each request to avoid detached instance issues
        stmt = select(User).where(User.id == user_id)
        result = await session.execute(stmt)
        fresh_user = result.scalar_one()
        return fresh_user

    app.dependency_overrides[get_current_user_from_token] = (
        override_get_current_user_from_token
    )
    yield client

    # Clean up this specific override
    if get_current_user_from_token in app.dependency_overrides:
        del app.dependency_overrides[get_current_user_from_token]


# ================================
# Repository Fixtures
# ================================


@pytest.fixture
async def user_repository(session: AsyncSession):
    """Create UserRepository instance with injected session - shared across modules."""

    return UserRepository(session)


@pytest.fixture
async def another_authenticated_client(
    client: AsyncClient, another_user: User, session: AsyncSession
) -> AsyncClient:
    """Create authenticated HTTP client for second user - shared across modules."""
    # Extract user_id early to avoid lazy loading issues
    user_id = another_user.id

    async def override_get_current_user_from_token():
        # Get a fresh user object from the database for each request to avoid detached instance issues
        stmt = select(User).where(User.id == user_id)
        result = await session.execute(stmt)
        fresh_user = result.scalar_one()
        return fresh_user

    app.dependency_overrides[get_current_user_from_token] = (
        override_get_current_user_from_token
    )
    yield client

    # Clean up this specific override
    if get_current_user_from_token in app.dependency_overrides:
        del app.dependency_overrides[get_current_user_from_token]
