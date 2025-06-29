"""Health check service with business logic."""

import time
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.config import get_settings
from ..core.database import get_db_health, get_pool_info
from .schemas import DatabaseHealthResponse, FullHealthResponse, SimpleHealthResponse


class HealthService:
    """Service for handling health check operations."""

    def __init__(self, session: AsyncSession | None = None):
        self.session = session
        self.settings = get_settings()

    def get_app_health(self) -> SimpleHealthResponse:
        """Get simple application health status."""
        return SimpleHealthResponse(
            status="healthy", environment=self.settings.environment, version="1.0.0"
        )

    async def get_database_health(self) -> DatabaseHealthResponse:
        """Check database connectivity with detailed status."""
        if not self.session:
            # Use the global database health check
            health_data = await get_db_health()

            if health_data["status"] == "healthy":
                return DatabaseHealthResponse(
                    status="healthy",
                    database="connected",
                    response_time_ms=0,  # Will be calculated below
                    pool_info=health_data.get("pool", {}),
                )
            else:
                return DatabaseHealthResponse(
                    status="unhealthy",
                    database="disconnected",
                    error=health_data.get("error", "Unknown error"),
                )

        # Use the session-based health check with timing
        try:
            start_time = time.time()
            await self.session.execute(text("SELECT 1"))
            response_time = (time.time() - start_time) * 1000

            # Get pool information
            pool_info = get_pool_info()

            return DatabaseHealthResponse(
                status="healthy",
                database="connected",
                response_time_ms=round(response_time, 2),
                pool_info=pool_info,
            )
        except Exception as e:
            return DatabaseHealthResponse(
                status="unhealthy", database="disconnected", error=str(e)
            )

    async def get_full_health(self) -> FullHealthResponse:
        """Get comprehensive health check."""
        app_health = self.get_app_health()
        db_health = await self.get_database_health()

        return FullHealthResponse(app=app_health, database=db_health)

    def get_system_info(self) -> dict[str, Any]:
        """Get additional system information."""
        return {
            "app_name": self.settings.app_name,
            "environment": self.settings.environment,
            "debug": self.settings.debug,
            "log_level": self.settings.log_level,
            "api_prefix": self.settings.api_v1_prefix,
            "database_pool_config": {
                "pool_size": self.settings.database_pool_size,
                "max_overflow": self.settings.database_max_overflow,
                "pool_timeout": self.settings.database_pool_timeout,
            },
        }
