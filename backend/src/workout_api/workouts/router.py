"""Workout API router."""

import logging
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response

from ..auth.dependencies import get_current_user_from_token
from ..users.models import User
from .dependencies import WorkoutServiceDep
from .schemas import (
    ExerciseExecutionRequest,
    ExerciseExecutionResponse,
    ExerciseExecutionUpdate,
    ExerciseReorderRequest,
    ExerciseReorderResponse,
    Page,
    Pagination,
    SetCreate,
    SetResponse,
    SetUpdate,
    WorkoutFilters,
    WorkoutFinishResponse,
    WorkoutResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/workouts", tags=["workouts"])

# Type aliases for dependencies
CurrentUser = Annotated[User, Depends(get_current_user_from_token)]


@router.get("/", response_model=Page[WorkoutResponse])
async def list_workouts(  # noqa: PLR0913
    service: WorkoutServiceDep,
    current_user: CurrentUser,
    start_date: str | None = None,
    end_date: str | None = None,
    finished: bool | None = None,
    page: int = 1,
    size: int = 20,
) -> Page[WorkoutResponse]:
    """List user workouts with optional filters and pagination."""
    user_id = current_user.id

    try:
        # Build filters
        filters = WorkoutFilters()
        if start_date:
            # Parse the datetime and remove timezone info to match database fields
            parsed_date = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
            filters.start_date = parsed_date.replace(tzinfo=None)
        if end_date:
            # Parse the datetime and remove timezone info to match database fields
            parsed_date = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
            filters.end_date = parsed_date.replace(tzinfo=None)
        if finished is not None:
            filters.finished = finished

        pagination = Pagination(page=page, size=size)

        return await service.get_workouts(filters, pagination, user_id)

    except ValueError as e:
        logger.error(f"Invalid date format in workout filters for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid date format. Use ISO 8601 format.",
        ) from e
    except Exception as e:
        logger.error(f"Error listing workouts for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        ) from e


@router.get("/{workout_id}", response_model=WorkoutResponse)
async def get_workout(
    workout_id: int,
    current_user: CurrentUser,
    service: WorkoutServiceDep,
) -> WorkoutResponse:
    """Get a single workout with full details."""
    user_id = current_user.id

    try:
        return await service.get_workout(workout_id, user_id)
    except Exception as e:
        logger.error(f"Error getting workout {workout_id} for user {user_id}: {e}")
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workout with ID {workout_id} not found",
            ) from e
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        ) from e


@router.post("/", response_model=WorkoutResponse, status_code=status.HTTP_201_CREATED)
async def create_workout(
    current_user: CurrentUser,
    service: WorkoutServiceDep,
) -> WorkoutResponse:
    """Create a new workout session."""
    user_id = current_user.id

    try:
        return await service.create_workout(user_id)
    except Exception as e:
        logger.error(f"Error creating workout for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        ) from e


@router.patch("/{workout_id}/finish", response_model=WorkoutFinishResponse)
async def finish_workout(
    workout_id: int,
    current_user: CurrentUser,
    service: WorkoutServiceDep,
) -> WorkoutFinishResponse:
    """Finish a workout session. Returns deleted=True if empty workout was deleted, deleted=False with workout data if finished."""
    user_id = current_user.id

    try:
        result = await service.finish_workout(workout_id, user_id)
        if result is None:
            # Empty workout was deleted
            return WorkoutFinishResponse(deleted=True, workout=None)
        else:
            # Workout was finished normally
            return WorkoutFinishResponse(deleted=False, workout=result)
    except Exception as e:
        logger.error(f"Error finishing workout {workout_id} for user {user_id}: {e}")
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workout with ID {workout_id} not found",
            ) from e
        if "already finished" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Workout is already finished",
            ) from e
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        ) from e


@router.delete("/{workout_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_workout(
    workout_id: int,
    current_user: CurrentUser,
    service: WorkoutServiceDep,
) -> Response:
    """Delete a workout."""
    user_id = current_user.id

    try:
        await service.delete_workout(workout_id, user_id)
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except Exception as e:
        logger.error(f"Error deleting workout {workout_id} for user {user_id}: {e}")
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workout with ID {workout_id} not found",
            ) from e
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        ) from e


# Exercise Execution endpoints

# IMPORTANT: Specific routes like /reorder must come BEFORE parameterized routes like /{exercise_id}
# to avoid FastAPI path matching conflicts


@router.patch(
    "/{workout_id}/exercise-executions/reorder", response_model=ExerciseReorderResponse
)
async def reorder_exercises(
    workout_id: int,
    data: ExerciseReorderRequest,
    current_user: CurrentUser,
    service: WorkoutServiceDep,
) -> ExerciseReorderResponse:
    """Reorder exercises in a workout."""
    user_id = current_user.id

    try:
        return await service.reorder_exercises(workout_id, data.exercise_ids, user_id)
    except Exception as e:
        logger.error(
            f"Error reordering exercises workout={workout_id} user={user_id}: {e}"
        )
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
            ) from e
        if "cannot modify finished workout" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot modify finished workout",
            ) from e
        if "mismatch" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
            ) from e
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        ) from e


@router.get(
    "/{workout_id}/exercise-executions/{exercise_id}",
    response_model=ExerciseExecutionResponse,
)
async def get_exercise_execution(
    workout_id: int,
    exercise_id: int,
    current_user: CurrentUser,
    service: WorkoutServiceDep,
) -> ExerciseExecutionResponse:
    """Get exercise execution with sets."""
    user_id = current_user.id

    try:
        return await service.get_exercise_execution(workout_id, exercise_id, user_id)
    except Exception as e:
        logger.error(
            f"Error getting exercise execution workout={workout_id} exercise={exercise_id} user={user_id}: {e}"
        )
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Exercise execution not found",
            ) from e
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        ) from e


@router.put(
    "/{workout_id}/exercise-executions/{exercise_id}",
    response_model=ExerciseExecutionResponse,
)
async def upsert_exercise_execution(
    workout_id: int,
    exercise_id: int,
    data: ExerciseExecutionRequest,
    current_user: CurrentUser,
    service: WorkoutServiceDep,
) -> ExerciseExecutionResponse:
    """Create or update exercise execution with full replacement of sets."""
    user_id = current_user.id

    try:
        return await service.upsert_exercise_execution(
            workout_id, exercise_id, data, user_id
        )
    except Exception as e:
        logger.error(
            f"Error upserting exercise execution workout={workout_id} exercise={exercise_id} user={user_id}: {e}"
        )
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
            ) from e
        if "cannot modify finished workout" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot modify finished workout",
            ) from e
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        ) from e


@router.delete(
    "/{workout_id}/exercise-executions/{exercise_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_exercise_execution(
    workout_id: int,
    exercise_id: int,
    current_user: CurrentUser,
    service: WorkoutServiceDep,
) -> Response:
    """Remove exercise from workout."""
    user_id = current_user.id

    try:
        await service.delete_exercise_execution(workout_id, exercise_id, user_id)
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except Exception as e:
        logger.error(
            f"Error deleting exercise execution workout={workout_id} exercise={exercise_id} user={user_id}: {e}"
        )
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Exercise execution not found",
            ) from e
        if "cannot modify finished workout" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot modify finished workout",
            ) from e
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        ) from e


@router.patch(
    "/{workout_id}/exercise-executions/{exercise_id}",
    response_model=ExerciseExecutionResponse,
)
async def update_exercise_execution(
    workout_id: int,
    exercise_id: int,
    data: ExerciseExecutionUpdate,
    current_user: CurrentUser,
    service: WorkoutServiceDep,
) -> ExerciseExecutionResponse:
    """Update exercise execution metadata (notes, order) without touching sets."""
    user_id = current_user.id

    try:
        return await service.update_exercise_execution(
            workout_id, exercise_id, data, user_id
        )
    except Exception as e:
        logger.error(
            f"Error updating exercise execution workout={workout_id} exercise={exercise_id} user={user_id}: {e}"
        )
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Exercise execution not found",
            ) from e
        if "cannot modify finished workout" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot modify finished workout",
            ) from e
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        ) from e


# Set endpoints
@router.post(
    "/{workout_id}/exercise-executions/{exercise_id}/sets",
    response_model=SetResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_set(
    workout_id: int,
    exercise_id: int,
    data: SetCreate,
    current_user: CurrentUser,
    service: WorkoutServiceDep,
) -> SetResponse:
    """Add a single set to an exercise execution."""
    user_id = current_user.id

    try:
        return await service.create_set(workout_id, exercise_id, data, user_id)
    except Exception as e:
        logger.error(
            f"Error creating set workout={workout_id} exercise={exercise_id} user={user_id}: {e}"
        )
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
            ) from e
        if "cannot modify finished workout" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot modify finished workout",
            ) from e
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        ) from e


@router.patch(
    "/{workout_id}/exercise-executions/{exercise_id}/sets/{set_id}",
    response_model=SetResponse,
)
async def update_set(  # noqa: PLR0913
    workout_id: int,
    exercise_id: int,
    set_id: int,
    data: SetUpdate,
    current_user: CurrentUser,
    service: WorkoutServiceDep,
) -> SetResponse:
    """Update a single set."""
    user_id = current_user.id

    try:
        return await service.update_set(workout_id, exercise_id, set_id, data, user_id)
    except Exception as e:
        logger.error(
            f"Error updating set workout={workout_id} exercise={exercise_id} set={set_id} user={user_id}: {e}"
        )
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
            ) from e
        if "cannot modify finished workout" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot modify finished workout",
            ) from e
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        ) from e


@router.delete(
    "/{workout_id}/exercise-executions/{exercise_id}/sets/{set_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_set(
    workout_id: int,
    exercise_id: int,
    set_id: int,
    current_user: CurrentUser,
    service: WorkoutServiceDep,
) -> Response:
    """Delete a single set."""
    user_id = current_user.id

    try:
        await service.delete_set(workout_id, exercise_id, set_id, user_id)
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except Exception as e:
        logger.error(
            f"Error deleting set workout={workout_id} exercise={exercise_id} set={set_id} user={user_id}: {e}"
        )
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
            ) from e
        if "cannot modify finished workout" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot modify finished workout",
            ) from e
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        ) from e
