import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from .config import get_settings

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Database connection and session management."""

    def __init__(self):
        self.settings = get_settings()
        self._engine = None
        self._session_maker = None
        self._initialize_engine()

    def _initialize_engine(self) -> None:
        """Initialize the database engine with proper configuration."""
        self._engine = create_async_engine(
            self.settings.database_url_async,
            pool_pre_ping=True,
            pool_size=self.settings.database_pool_size,
            max_overflow=self.settings.database_max_overflow,
            pool_timeout=self.settings.database_pool_timeout,
            echo=self.settings.debug and self.settings.is_development,
            future=True,
        )

        # Engine configured with connection pooling

        # Create session factory
        self._session_maker = async_sessionmaker(
            bind=self._engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=True,
            autocommit=False,
        )

        logger.info("Database engine initialized")

    @property
    def engine(self):
        """Get the database engine."""
        if self._engine is None:
            self._initialize_engine()
        return self._engine

    @property
    def session_maker(self):
        """Get the session maker."""
        if self._session_maker is None:
            self._initialize_engine()
        return self._session_maker

    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get database session with proper cleanup. Transaction commit is service layer responsibility."""
        if self._session_maker is None:
            self._initialize_engine()

        async with self._session_maker() as session:
            try:
                yield session
                logger.debug("Database session yielded successfully")
            except Exception as e:
                await session.rollback()
                logger.error(f"Database session rolled back due to error: {e}")
                raise
            finally:
                await session.close()
                logger.debug("Database session closed")

    @asynccontextmanager
    async def get_session_context(self) -> AsyncGenerator[AsyncSession, None]:
        """Get database session as context manager for manual transaction control."""
        if self._session_maker is None:
            self._initialize_engine()

        async with self._session_maker() as session:
            try:
                yield session
            finally:
                await session.close()

    async def check_connection(self) -> dict[str, Any]:
        """Check database connection health."""
        try:
            async with self.get_session_context() as session:
                result = await session.execute(text("SELECT 1 as health_check"))
                row = result.fetchone()

                if row and row[0] == 1:
                    pool_status = self.get_pool_status()
                    return {
                        "status": "healthy",
                        "connection": "active",
                        "pool": pool_status,
                    }
                else:
                    return {
                        "status": "unhealthy",
                        "connection": "failed",
                        "error": "Health check query failed",
                    }
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {"status": "unhealthy", "connection": "failed", "error": str(e)}

    def get_pool_status(self) -> dict[str, Any]:
        """Get connection pool status information."""
        if self._engine is None:
            return {"status": "not_initialized"}

        pool = self._engine.pool
        try:
            return {
                "size": pool.size(),
                "checked_in": pool.checkedin(),
                "checked_out": pool.checkedout(),
                "overflow": pool.overflow(),
                "status": "active",
            }
        except AttributeError as e:
            logger.debug(f"Pool status method not available: {e}")
            return {"status": "active", "note": "detailed pool status not available"}

    async def close(self) -> None:
        """Close database engine and all connections."""
        if self._engine:
            await self._engine.dispose()
            logger.info("Database engine disposed")


# Global database manager instance
db_manager = DatabaseManager()


# Dependency for FastAPI
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Get database session dependency for FastAPI."""
    async for session in db_manager.get_session():
        yield session


# Convenience functions
async def get_db_health() -> dict[str, Any]:
    """Get database health status."""
    return await db_manager.check_connection()


def get_pool_info() -> dict[str, Any]:
    """Get connection pool information."""
    return db_manager.get_pool_status()
