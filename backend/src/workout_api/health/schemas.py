"""Health check response schemas."""

from typing import Literal

from pydantic import BaseModel


class SimpleHealthResponse(BaseModel):
    """Simple application health response."""

    status: Literal["healthy", "unhealthy"]
    environment: str
    version: str


class DatabaseHealthResponse(BaseModel):
    """Database health check response."""

    status: Literal["healthy", "unhealthy"]
    database: Literal["connected", "disconnected"]
    response_time_ms: float | None = None


class FullHealthResponse(BaseModel):
    """Comprehensive health check response."""

    app: SimpleHealthResponse
    database: DatabaseHealthResponse
