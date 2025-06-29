"""Test configuration with anyio and transaction isolation."""

from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from testcontainers.postgres import PostgresContainer

from workout_api.core.database import get_session
from workout_api.core.main import app
from workout_api.shared.base_model import Base

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
