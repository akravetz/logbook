"""Exercise dependencies for FastAPI."""

from functools import lru_cache
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import get_session
from .repository import ExerciseRepository
from .service import ExerciseService


@lru_cache
def get_exercise_repository(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ExerciseRepository:
    """Get exercise repository instance."""
    return ExerciseRepository(session)


@lru_cache
def get_exercise_service(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ExerciseService:
    """Get exercise service instance."""
    return ExerciseService(session)


# Type aliases for dependency injection
ExerciseRepositoryDep = Annotated[ExerciseRepository, Depends(get_exercise_repository)]
ExerciseServiceDep = Annotated[ExerciseService, Depends(get_exercise_service)]
