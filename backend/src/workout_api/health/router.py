"""Health check router with FastAPI endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import get_session
from .schemas import (
    DatabaseHealthResponse,
    FullHealthResponse,
    SimpleHealthResponse,
    SystemInfoResponse,
)
from .service import HealthService

router = APIRouter()


def get_health_service(session: AsyncSession = Depends(get_session)) -> HealthService:
    """Get health service with database session."""
    return HealthService(session)


def get_health_service_no_db() -> HealthService:
    """Get health service without database session."""
    return HealthService()


@router.get("/", response_model=SimpleHealthResponse)
async def simple_health_check(
    health_service: HealthService = Depends(get_health_service_no_db),
):
    """Simple health check - is the application running?"""
    return health_service.get_app_health()


@router.get("/db", response_model=DatabaseHealthResponse)
async def database_health_check(
    health_service: HealthService = Depends(get_health_service),
):
    """Database health check - can we connect to the database?"""
    return await health_service.get_database_health()


@router.get("/full", response_model=FullHealthResponse)
async def full_health_check(
    health_service: HealthService = Depends(get_health_service),
):
    """Comprehensive health check - app and database status."""
    return await health_service.get_full_health()


@router.get("/system", response_model=SystemInfoResponse)
async def system_info(
    health_service: HealthService = Depends(get_health_service_no_db),
):
    """Get system configuration and runtime information."""
    return health_service.get_system_info()
