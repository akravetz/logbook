"""Health check service with business logic."""

import time

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.config import get_settings
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
        """Check database connectivity with SELECT 1."""
        if not self.session:
            return DatabaseHealthResponse(status="unhealthy", database="disconnected")

        try:
            start_time = time.time()
            await self.session.execute(text("SELECT 1"))
            response_time = (time.time() - start_time) * 1000

            return DatabaseHealthResponse(
                status="healthy",
                database="connected",
                response_time_ms=round(response_time, 2),
            )
        except Exception:
            return DatabaseHealthResponse(status="unhealthy", database="disconnected")

    async def get_full_health(self) -> FullHealthResponse:
        """Get comprehensive health check."""
        app_health = self.get_app_health()
        db_health = await self.get_database_health()

        return FullHealthResponse(app=app_health, database=db_health)
