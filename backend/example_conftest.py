"""Pytest configuration and fixtures."""

import asyncio
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from app.core.config import Settings
from app.main import app
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel
from testcontainers.postgres import PostgresContainer


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def postgres_testcontainer():
    """Create a session-scoped PostgreSQL testcontainer for integration tests."""
    container = PostgresContainer("postgres:16-alpine")
    container.start()
    yield container
    container.stop()


@pytest.fixture
def test_settings(monkeypatch) -> Settings:
    """Create test settings with required environment variables."""
    # Set required environment variables for testing
    monkeypatch.setenv("JWT_SECRET_KEY", "test-secret-key")
    monkeypatch.setenv("GOOGLE_CLIENT_ID", "test-google-client-id")
    monkeypatch.setenv("GOOGLE_CLIENT_SECRET", "test-google-client-secret")
    monkeypatch.setenv(
        "DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/test_db"
    )
    monkeypatch.setenv("APP_ENV", "testing")

    # Clear the settings cache to ensure fresh instance
    from app.core.config import get_settings

    get_settings.cache_clear()

    return Settings()


@pytest.fixture
async def test_engine(test_settings):
    """Create a test database engine."""
    engine = create_async_engine(
        str(test_settings.database_url),
        echo=False,
        pool_size=5,
        max_overflow=0,
    )

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    yield engine

    # Drop tables and close engine
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
async def test_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session."""
    async_session = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )

    async with async_session() as session:
        yield session
        await session.rollback()  # Rollback any changes made during the test


@pytest.fixture
def anyio_backend() -> str:
    """Use asyncio backend for anyio."""
    return "asyncio"


@pytest_asyncio.fixture
async def client(postgres_testcontainer) -> AsyncGenerator[AsyncClient, None]:
    """Create an async test client for the FastAPI app with testcontainer database."""
    from app.core.database import get_db

    # Create async engine for testcontainer database
    test_database_url = postgres_testcontainer.get_connection_url(driver="asyncpg")
    test_engine = create_async_engine(test_database_url, echo=False)
    test_async_session = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )

    async def get_test_db():
        async with test_async_session() as session:
            yield session

    # Override the database dependency
    app.dependency_overrides[get_db] = get_test_db

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            yield ac
    finally:
        # Clean up dependency overrides and dispose engine
        app.dependency_overrides.clear()
        await test_engine.dispose()


# Markers for different test types
def pytest_configure(config):
    """Configure custom pytest markers."""
    config.addinivalue_line("markers", "unit: mark test as a unit test")
    config.addinivalue_line("markers", "integration: mark test as an integration test")
    config.addinivalue_line("markers", "slow: mark test as slow running")
