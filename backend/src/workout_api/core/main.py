"""Main FastAPI application."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from hypercorn.config import Config

from ..auth.router import router as auth_router
from ..exercises.router import router as exercises_router
from ..health.router import router as health_router
from ..shared.exceptions import (
    AuthenticationError,
    BusinessRuleError,
    DuplicateError,
    NotFoundError,
    PermissionError,
    ValidationError,
    WorkoutAPIException,
)
from ..users.router import router as users_router
from ..workouts.router import router as workouts_router
from .config import get_settings
from .database import db_manager
from .logging import setup_logging

# Initialize logging first
setup_logging()
logger = logging.getLogger("workout_api.main")

settings = get_settings()


def get_hypercorn_config() -> Config:
    """Get hypercorn configuration."""
    config = Config()

    # Basic server settings
    config.bind = [f"{settings.host}:{settings.port}"]
    config.use_reloader = settings.reload and settings.is_development
    config.loglevel = settings.log_level.lower()
    config.access_log_format = (
        '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'
    )

    # Enable HTTP/2 support
    config.h2 = settings.enable_http2
    config.alpn_protocols = (
        ["h2", "http/1.1"] if settings.enable_http2 else ["http/1.1"]
    )

    # Performance settings
    config.workers = settings.workers if settings.is_production else 1
    config.keep_alive_timeout = settings.keep_alive_timeout
    config.max_requests = settings.max_requests
    config.max_requests_jitter = settings.max_requests_jitter
    config.h2_max_concurrent_streams = settings.h2_max_concurrent_streams

    # Server identification
    config.server_names = ["localhost", "127.0.0.1"] if settings.is_development else []

    # Environment-specific settings
    if settings.is_development:
        config.debug = True
        config.access_log = True
        config.reload = True
        config.include_server_header = True
    else:
        config.debug = False
        config.access_log = True
        config.reload = False
        config.include_server_header = False
        config.graceful_timeout = 30
        config.shutdown_timeout = 30

    return config


def get_server_config() -> dict[str, str | int | bool]:
    """Get server configuration for backward compatibility."""
    return {
        "host": settings.host,
        "port": settings.port,
        "reload": settings.reload,
        "log_level": settings.log_level.lower(),
        "access_log": settings.debug,
        "use_colors": settings.is_development,
    }


@asynccontextmanager
async def lifespan(app: FastAPI):  # noqa: ARG001
    """Application lifespan events."""
    # Startup
    logger.info(f"Starting {settings.app_name} in {settings.environment} mode")
    logger.info(f"Debug mode: {settings.debug}")
    logger.info(f"Log level: {settings.log_level}")
    logger.info(f"Server will run on {settings.host}:{settings.port}")
    logger.info(f"Auto-reload: {settings.reload}")
    logger.info(f"Database URL configured: {bool(settings.database_url)}")

    # Log API configuration
    logger.info(f"API v1 prefix: {settings.api_v1_prefix}")
    logger.info(
        f"Documentation URL: {settings.docs_url if not settings.is_production else 'disabled'}"
    )
    logger.info(f"CORS origins: {settings.allowed_origins}")

    # Database connectivity check
    try:
        health_result = await db_manager.check_connection()
        if health_result["status"] == "healthy":
            logger.info("Database connection successful")
        else:
            logger.warning(
                f"Database connection issue: {health_result.get('error', 'Unknown error')}"
            )
    except Exception as e:
        logger.error(f"Database connection check failed: {e}")

    yield

    # Shutdown
    logger.info("Shutting down application")
    await db_manager.close()
    logger.info("Application shutdown complete")


# Create FastAPI application with lifespan
app = FastAPI(
    title=settings.app_name,
    description="A workout tracking API built with FastAPI",
    version="1.0.0",
    debug=settings.debug,
    docs_url=settings.docs_url if not settings.is_production else None,
    redoc_url=settings.redoc_url if not settings.is_production else None,
    openapi_url=settings.openapi_url if not settings.is_production else None,
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=settings.allowed_methods,
    allow_headers=settings.allowed_headers,
)


# Exception handlers
@app.exception_handler(NotFoundError)
async def not_found_handler(request: Request, exc: NotFoundError):
    """Handle not found errors."""
    logger.warning(f"Not found error on {request.url}: {exc}")
    return JSONResponse(
        status_code=404, content={"error": str(exc), "type": "not_found"}
    )


@app.exception_handler(DuplicateError)
async def duplicate_handler(request: Request, exc: DuplicateError):
    """Handle duplicate resource errors."""
    logger.warning(f"Duplicate error on {request.url}: {exc}")
    return JSONResponse(
        status_code=409, content={"error": str(exc), "type": "duplicate"}
    )


@app.exception_handler(ValidationError)
async def validation_handler(request: Request, exc: ValidationError):
    """Handle validation errors."""
    logger.warning(f"Validation error on {request.url}: {exc}")
    return JSONResponse(
        status_code=422, content={"error": str(exc), "type": "validation"}
    )


@app.exception_handler(AuthenticationError)
async def authentication_handler(request: Request, exc: AuthenticationError):
    """Handle authentication errors."""
    logger.warning(f"Authentication error on {request.url}: {exc}")
    return JSONResponse(
        status_code=401, content={"error": str(exc), "type": "authentication"}
    )


@app.exception_handler(PermissionError)
async def permission_handler(request: Request, exc: PermissionError):
    """Handle permission errors."""
    logger.warning(f"Permission error on {request.url}: {exc}")
    return JSONResponse(
        status_code=403, content={"error": str(exc), "type": "permission"}
    )


@app.exception_handler(BusinessRuleError)
async def business_rule_handler(request: Request, exc: BusinessRuleError):
    """Handle business rule errors."""
    logger.warning(f"Business rule error on {request.url}: {exc}")
    return JSONResponse(
        status_code=400, content={"error": str(exc), "type": "business_rule"}
    )


@app.exception_handler(WorkoutAPIException)
async def generic_api_handler(request: Request, exc: WorkoutAPIException):
    """Handle generic API errors."""
    logger.error(f"API error on {request.url}: {exc}")
    return JSONResponse(
        status_code=500, content={"error": str(exc), "type": "api_error"}
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions."""
    logger.error(f"Unexpected error on {request.url}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "type": "server_error",
            "detail": str(exc) if settings.debug else "An unexpected error occurred",
        },
    )


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": f"Welcome to the {settings.app_name}",
        "environment": settings.environment,
        "version": "1.0.0",
        "docs": settings.docs_url if not settings.is_production else None,
        "health": "/health",
        "api_prefix": settings.api_v1_prefix,
    }


# Include routers
app.include_router(health_router, prefix="/health", tags=["Health"])

# Authentication router
app.include_router(
    auth_router, prefix=f"{settings.api_v1_prefix}/auth", tags=["Authentication"]
)

# Additional routers
app.include_router(users_router, prefix=f"{settings.api_v1_prefix}")
app.include_router(exercises_router, prefix=f"{settings.api_v1_prefix}")
app.include_router(workouts_router, prefix=f"{settings.api_v1_prefix}")


# Export server configuration and app
__all__ = ["app", "get_hypercorn_config", "get_server_config", "settings"]
