"""Test configuration with transaction isolation."""

import asyncio
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from testcontainers.postgres import PostgresContainer

from workout_api.core.database import get_session
from workout_api.core.main import app
from workout_api.shared.base_model import Base


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def postgres_container():
    """Start PostgreSQL container for testing."""
    # Use asyncpg driver explicitly for async SQLAlchemy
    with PostgresContainer("postgres:16", driver="asyncpg") as postgres:
        yield postgres


@pytest.fixture(scope="session")
def test_engine(postgres_container):
    """Create test database engine."""
    # Get connection URL with asyncpg driver already configured
    database_url = postgres_container.get_connection_url()

    engine = create_async_engine(
        database_url,
        echo=False,  # Set to True for SQL debugging
    )

    yield engine


@pytest.fixture(scope="session")
async def setup_database(test_engine):
    """Setup database tables."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await test_engine.dispose()


@pytest_asyncio.fixture
async def session(test_engine, setup_database) -> AsyncGenerator[AsyncSession, None]:  # noqa: ARG001
    """Create test session with transaction isolation."""
    async with (
        test_engine.begin() as connection,
        AsyncSession(
            bind=connection, join_transaction_mode="create_savepoint"
        ) as session,
    ):
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def client(session: AsyncSession) -> TestClient:
    """Create test client with database dependency override."""

    async def override_get_session():
        yield session

    app.dependency_overrides[get_session] = override_get_session

    with TestClient(app) as test_client:
        yield test_client

    # Clean up
    app.dependency_overrides.clear()


@pytest.fixture
def anyio_backend():
    """Configure anyio backend for async tests."""
    return "asyncio"
