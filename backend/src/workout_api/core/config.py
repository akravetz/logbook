import os
from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration settings."""

    def __hash__(self) -> int:
        """Make Settings hashable for use with @lru_cache."""

        # Create a hash based on all the field values, converting unhashable types
        def make_hashable(obj):
            """Convert unhashable types to hashable ones."""
            if isinstance(obj, list):
                return tuple(obj)
            elif isinstance(obj, dict):
                return tuple(sorted(obj.items()))
            return obj

        items = tuple(
            sorted((k, make_hashable(v)) for k, v in self.model_dump().items())
        )
        return hash(items)

    def __eq__(self, other: object) -> bool:
        """Define equality for Settings objects."""
        if not isinstance(other, Settings):
            return False
        return self.model_dump() == other.model_dump()

    # Application settings
    app_name: str = "Workout API"
    environment: Literal["development", "test", "production"] = "development"
    debug: bool = Field(default=False, description="Enable debug mode")
    log_level: str = Field(default="INFO", description="Logging level")

    # Server settings
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8080, description="Server port")
    reload: bool = Field(default=False, description="Auto-reload on code changes")

    # Database
    database_url: str = Field(description="Database connection URL")
    database_pool_size: int = Field(
        default=10, description="Database connection pool size"
    )
    database_max_overflow: int = Field(
        default=20, description="Database max overflow connections"
    )
    database_pool_timeout: int = Field(
        default=30, description="Database pool timeout in seconds"
    )

    # Security & JWT Authentication
    secret_key: str = Field(description="General application secret key", min_length=32)
    jwt_secret_key: str = Field(
        description="Separate secret key for JWT tokens", min_length=32, default=""
    )
    jwt_algorithm: str = Field(default="HS256", description="JWT signing algorithm")
    access_token_expire_minutes: int = Field(
        default=360, description="Access token expiration in minutes (6 hours)"
    )
    refresh_token_expire_days: int = Field(
        default=7, description="Refresh token expiration in days"
    )

    # Session Management
    session_secret_key: str = Field(
        description="Secret key for session middleware (OAuth state management)",
        default="",
    )
    session_max_age: int = Field(
        default=3 * 60 * 60,  # 3 hours
        description="Session max age in seconds",
    )

    # Google OAuth
    google_client_id: str = Field(description="Google OAuth client ID")
    google_client_secret: str = Field(description="Google OAuth client secret")
    google_redirect_uri: str = Field(
        default="http://localhost:8080/api/v1/auth/google/callback",
        description="Google OAuth redirect URI",
    )
    google_discovery_url: str = Field(
        default="https://accounts.google.com/.well-known/openid_configuration",
        description="Google OAuth discovery URL",
    )

    # CORS
    allowed_origins: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:8080"],
        description="Allowed CORS origins",
    )
    allowed_methods: list[str] = Field(
        default=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        description="Allowed HTTP methods",
    )
    allowed_headers: list[str] = Field(
        default=["*"], description="Allowed HTTP headers"
    )

    # Hypercorn-specific settings
    workers: int = Field(default=1, description="Number of worker processes")
    worker_class: str = Field(
        default="asyncio", description="Worker class (asyncio, uvloop, trio)"
    )
    keep_alive_timeout: int = Field(
        default=75, description="Keep alive timeout in seconds"
    )
    max_requests: int = Field(
        default=1000, description="Max requests per worker before restart"
    )
    max_requests_jitter: int = Field(
        default=100, description="Random jitter for max_requests"
    )

    # HTTP/2 and performance
    enable_http2: bool = Field(default=True, description="Enable HTTP/2 support")
    h2_max_concurrent_streams: int = Field(
        default=100, description="HTTP/2 max concurrent streams"
    )

    # API settings
    api_v1_prefix: str = Field(default="/api/v1", description="API v1 prefix")
    docs_url: str = Field(default="/docs", description="API documentation URL")
    redoc_url: str = Field(default="/redoc", description="ReDoc URL")
    openapi_url: str = Field(default="/openapi.json", description="OpenAPI schema URL")

    model_config = SettingsConfigDict(
        env_file=".env.test" if os.getenv("ENVIRONMENT") == "test" else ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @field_validator("environment")
    def validate_environment(cls, v: str) -> str:
        """Validate environment value."""
        if v not in ("development", "test", "production"):
            raise ValueError("Environment must be development, test, or production")
        return v

    @field_validator("log_level")
    def validate_log_level(cls, v: str) -> str:
        """Validate log level."""
        valid_levels = ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")
        if v.upper() not in valid_levels:
            raise ValueError(f"Log level must be one of: {valid_levels}")
        return v.upper()

    def model_post_init(self, __context) -> None:
        """Post-initialization to set default secrets if not provided."""
        if not self.jwt_secret_key:
            # Use main secret_key as fallback for JWT if jwt_secret_key not set
            object.__setattr__(self, "jwt_secret_key", self.secret_key)

        if not self.session_secret_key:
            # Use main secret_key as fallback for sessions if session_secret_key not set
            object.__setattr__(self, "session_secret_key", self.secret_key)

        # Validate that session_secret_key is long enough after setting fallback
        if len(self.session_secret_key) < 32:
            raise ValueError("session_secret_key must be at least 32 characters long")

    @property
    def database_url_async(self) -> str:
        """Convert sync PostgreSQL URL to async."""
        return str(self.database_url).replace("postgresql://", "postgresql+asyncpg://")

    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.environment == "development"

    @property
    def is_test(self) -> bool:
        """Check if running in test mode."""
        return self.environment == "test"

    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.environment == "production"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
