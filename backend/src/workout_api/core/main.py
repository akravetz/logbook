"""Main FastAPI application."""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

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
from .config import get_settings

settings = get_settings()

# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    description="A workout tracking API built with FastAPI",
    version="1.0.0",
    debug=settings.debug,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handlers
@app.exception_handler(NotFoundError)
async def not_found_handler(_request: Request, exc: NotFoundError):
    """Handle not found errors."""
    return JSONResponse(
        status_code=404, content={"error": str(exc), "type": "not_found"}
    )


@app.exception_handler(DuplicateError)
async def duplicate_handler(_request: Request, exc: DuplicateError):
    """Handle duplicate resource errors."""
    return JSONResponse(
        status_code=409, content={"error": str(exc), "type": "duplicate"}
    )


@app.exception_handler(ValidationError)
async def validation_handler(_request: Request, exc: ValidationError):
    """Handle validation errors."""
    return JSONResponse(
        status_code=422, content={"error": str(exc), "type": "validation"}
    )


@app.exception_handler(AuthenticationError)
async def authentication_handler(_request: Request, exc: AuthenticationError):
    """Handle authentication errors."""
    return JSONResponse(
        status_code=401, content={"error": str(exc), "type": "authentication"}
    )


@app.exception_handler(PermissionError)
async def permission_handler(_request: Request, exc: PermissionError):
    """Handle permission errors."""
    return JSONResponse(
        status_code=403, content={"error": str(exc), "type": "permission"}
    )


@app.exception_handler(BusinessRuleError)
async def business_rule_handler(_request: Request, exc: BusinessRuleError):
    """Handle business rule errors."""
    return JSONResponse(
        status_code=400, content={"error": str(exc), "type": "business_rule"}
    )


@app.exception_handler(WorkoutAPIException)
async def generic_api_handler(_request: Request, exc: WorkoutAPIException):
    """Handle generic API errors."""
    return JSONResponse(
        status_code=500, content={"error": str(exc), "type": "api_error"}
    )


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Welcome to the Workout API",
        "docs": "/docs",
        "health": "/health",
    }


# Include routers
app.include_router(health_router, prefix="/health", tags=["health"])

# Additional routers will be added here
# from ..auth.router import router as auth_router
# from ..users.router import router as users_router
# from ..exercises.router import router as exercises_router
# from ..workouts.router import router as workouts_router

# app.include_router(auth_router, prefix="/api/v1/auth", tags=["auth"])
# app.include_router(users_router, prefix="/api/v1/users", tags=["users"])
# app.include_router(exercises_router, prefix="/api/v1/exercises", tags=["exercises"])
# app.include_router(workouts_router, prefix="/api/v1/workouts", tags=["workouts"])
