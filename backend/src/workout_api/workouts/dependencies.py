"""FastAPI dependencies for workout module."""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import get_session
from .repository import WorkoutRepository
from .service import WorkoutService


def get_workout_repository(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> WorkoutRepository:
    """Get workout repository instance."""
    return WorkoutRepository(session)


def get_workout_service(
    repository: Annotated[WorkoutRepository, Depends(get_workout_repository)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> WorkoutService:
    """Get workout service instance."""
    return WorkoutService(repository, session)


# Type aliases for dependency injection
WorkoutRepositoryDep = Annotated[WorkoutRepository, Depends(get_workout_repository)]
WorkoutServiceDep = Annotated[WorkoutService, Depends(get_workout_service)]
