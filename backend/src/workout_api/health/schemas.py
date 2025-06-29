"""Health check response schemas."""

from typing import Any, Literal

from pydantic import BaseModel, Field


class SimpleHealthResponse(BaseModel):
    """Simple application health response."""

    status: Literal["healthy", "unhealthy"]
    environment: str
    version: str


class PoolInfoResponse(BaseModel):
    """Database connection pool information."""

    size: int = Field(description="Pool size")
    checked_in: int = Field(description="Connections checked in")
    checked_out: int = Field(description="Connections checked out")
    overflow: int = Field(description="Overflow connections")
    invalid: int = Field(description="Invalid connections")
    status: str = Field(description="Pool status")


class DatabaseHealthResponse(BaseModel):
    """Database health check response."""

    status: Literal["healthy", "unhealthy"]
    database: Literal["connected", "disconnected"]
    response_time_ms: float | None = Field(
        default=None, description="Database response time in milliseconds"
    )
    pool_info: dict[str, Any] | None = Field(
        default=None, description="Connection pool information"
    )
    error: str | None = Field(default=None, description="Error message if unhealthy")


class SystemInfoResponse(BaseModel):
    """System configuration information."""

    app_name: str
    environment: str
    debug: bool
    log_level: str
    api_prefix: str
    database_pool_config: dict[str, Any]


class FullHealthResponse(BaseModel):
    """Comprehensive health check response."""

    app: SimpleHealthResponse
    database: DatabaseHealthResponse
