"""Exercise API endpoints."""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from ..auth.dependencies import get_current_user_from_token, get_current_user_optional
from ..shared.exceptions import NotFoundError, ValidationError
from ..users.models import User
from .dependencies import ExerciseServiceDep
from .models import ExerciseModality
from .schemas import (
    ExerciseCreate,
    ExerciseFilters,
    ExerciseResponse,
    ExerciseUpdate,
    Page,
    Pagination,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/exercises", tags=["exercises"])


@router.get(
    "/",
    response_model=Page[ExerciseResponse],
    summary="Search exercises",
    description="Search and filter exercises with pagination. Public endpoint - shows only system exercises unless authenticated.",
)
async def search_exercises(  # noqa: PLR0913
    exercise_service: ExerciseServiceDep,
    current_user: Annotated[User | None, Depends(get_current_user_optional)] = None,
    name: Annotated[
        str | None, Query(description="Filter by exercise name (partial match)")
    ] = None,
    body_part: Annotated[str | None, Query(description="Filter by body part")] = None,
    modality: Annotated[
        str | None, Query(description="Filter by exercise modality")
    ] = None,
    is_user_created: Annotated[
        bool | None, Query(description="Filter by user-created vs system exercises")
    ] = None,
    created_by_user_id: Annotated[
        int | None, Query(description="Filter exercises created by specific user")
    ] = None,
    page: Annotated[int, Query(ge=1, description="Page number (1-based)")] = 1,
    size: Annotated[int, Query(ge=1, le=100, description="Page size (max 100)")] = 20,
) -> Page[ExerciseResponse]:
    """Search exercises with filters and pagination."""
    # Get user ID if authenticated
    user_id = current_user.id if current_user else None

    try:
        # Parse modality if provided
        modality_enum = None
        if modality:
            try:
                modality_enum = ExerciseModality(modality.upper())
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid modality: {modality}",
                ) from None

        filters = ExerciseFilters(
            name=name,
            body_part=body_part,
            modality=modality_enum,
            is_user_created=is_user_created,
            created_by_user_id=created_by_user_id,
        )
        pagination = Pagination(page=page, size=size)

        return await exercise_service.search_exercises(filters, pagination, user_id)

    except ValidationError as e:
        logger.warning(f"Validation error searching exercises for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e
    except Exception as e:
        logger.error(f"Error searching exercises for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        ) from e


@router.get(
    "/body-parts",
    response_model=list[str],
    summary="Get available body parts",
    description="Get list of all available body parts from exercises user can access.",
)
async def get_body_parts(
    exercise_service: ExerciseServiceDep,
    current_user: Annotated[User | None, Depends(get_current_user_optional)] = None,
) -> list[str]:
    """Get available body parts."""
    # Get user ID if authenticated
    user_id = current_user.id if current_user else None

    try:
        return await exercise_service.get_available_body_parts(user_id)
    except Exception as e:
        logger.error(f"Error getting body parts for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        ) from e


@router.get(
    "/modalities",
    response_model=list[str],
    summary="Get available modalities",
    description="Get list of all available exercise modalities.",
)
async def get_modalities() -> list[str]:
    """Get available exercise modalities."""
    try:
        return [modality.value for modality in ExerciseModality]
    except Exception as e:
        logger.error(f"Error getting modalities: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        ) from e


@router.get(
    "/system",
    response_model=Page[ExerciseResponse],
    summary="Get system exercises",
    description="Get system exercises with pagination.",
)
async def get_system_exercises(
    exercise_service: ExerciseServiceDep,
    page: Annotated[int, Query(ge=1, description="Page number (1-based)")] = 1,
    size: Annotated[int, Query(ge=1, le=100, description="Page size (max 100)")] = 20,
) -> Page[ExerciseResponse]:
    """Get system exercises."""
    try:
        pagination = Pagination(page=page, size=size)
        return await exercise_service.get_system_exercises(pagination)
    except Exception as e:
        logger.error(f"Error getting system exercises: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        ) from e


@router.get(
    "/my-exercises",
    response_model=Page[ExerciseResponse],
    summary="Get user's own exercises",
    description="Get exercises created by the current user.",
)
async def get_my_exercises(
    current_user: Annotated[User, Depends(get_current_user_from_token)],
    exercise_service: ExerciseServiceDep,
    page: Annotated[int, Query(ge=1, description="Page number (1-based)")] = 1,
    size: Annotated[int, Query(ge=1, le=100, description="Page size (max 100)")] = 20,
) -> Page[ExerciseResponse]:
    """Get current user's exercises."""
    # Store user ID early to avoid lazy loading in exception handlers
    user_id = current_user.id

    try:
        pagination = Pagination(page=page, size=size)
        return await exercise_service.get_user_exercises(user_id, pagination)
    except Exception as e:
        logger.error(f"Error getting exercises for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        ) from e


@router.get(
    "/by-body-part/{body_part}",
    response_model=Page[ExerciseResponse],
    summary="Get exercises by body part",
    description="Get exercises filtered by body part with pagination.",
)
async def get_exercises_by_body_part(
    body_part: str,
    exercise_service: ExerciseServiceDep,
    current_user: Annotated[User | None, Depends(get_current_user_optional)] = None,
    page: Annotated[int, Query(ge=1, description="Page number (1-based)")] = 1,
    size: Annotated[int, Query(ge=1, le=100, description="Page size (max 100)")] = 20,
) -> Page[ExerciseResponse]:
    """Get exercises by body part."""
    # Get user ID if authenticated
    user_id = current_user.id if current_user else None

    try:
        pagination = Pagination(page=page, size=size)
        return await exercise_service.get_by_body_part(body_part, pagination, user_id)
    except Exception as e:
        logger.error(
            f"Error getting exercises by body part {body_part} for user {user_id}: {e}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        ) from e


@router.get(
    "/by-modality/{modality}",
    response_model=Page[ExerciseResponse],
    summary="Get exercises by modality",
    description="Get exercises filtered by modality with pagination.",
)
async def get_exercises_by_modality(
    modality: str,
    exercise_service: ExerciseServiceDep,
    current_user: Annotated[User | None, Depends(get_current_user_optional)] = None,
    page: Annotated[int, Query(ge=1, description="Page number (1-based)")] = 1,
    size: Annotated[int, Query(ge=1, le=100, description="Page size (max 100)")] = 20,
) -> Page[ExerciseResponse]:
    """Get exercises by modality."""
    # Get user ID if authenticated
    user_id = current_user.id if current_user else None

    try:
        # Validate modality
        try:
            ExerciseModality(modality.upper())
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid modality: {modality}",
            ) from None

        pagination = Pagination(page=page, size=size)
        return await exercise_service.get_by_modality(modality, pagination, user_id)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error getting exercises by modality {modality} for user {user_id}: {e}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        ) from e


@router.get(
    "/{exercise_id}",
    response_model=ExerciseResponse,
    summary="Get exercise by ID",
    description="Get a specific exercise by ID. Public endpoint - shows only system exercises unless authenticated.",
)
async def get_exercise(
    exercise_id: int,
    exercise_service: ExerciseServiceDep,
    current_user: Annotated[User | None, Depends(get_current_user_optional)] = None,
) -> ExerciseResponse:
    """Get exercise by ID."""
    # Get user ID if authenticated
    user_id = current_user.id if current_user else None

    try:
        return await exercise_service.get_exercise_by_id(exercise_id, user_id)
    except NotFoundError as e:
        logger.warning(f"Exercise {exercise_id} not found for user {user_id}: {e}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except Exception as e:
        logger.error(f"Error getting exercise {exercise_id} for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        ) from e


@router.post(
    "/",
    response_model=ExerciseResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create exercise",
    description="Create a new user exercise.",
)
async def create_exercise(
    exercise_data: ExerciseCreate,
    current_user: Annotated[User, Depends(get_current_user_from_token)],
    exercise_service: ExerciseServiceDep,
) -> ExerciseResponse:
    """Create a new exercise."""
    # Store user ID early to avoid lazy loading in exception handlers
    user_id = current_user.id

    try:
        return await exercise_service.create_user_exercise(exercise_data, user_id)
    except ValidationError as e:
        logger.warning(f"Validation error creating exercise for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e
    except Exception as e:
        logger.error(f"Error creating exercise for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        ) from e


@router.patch(
    "/{exercise_id}",
    response_model=ExerciseResponse,
    summary="Update exercise",
    description="Update an existing user exercise. Users can only update their own exercises.",
)
async def update_exercise(
    exercise_id: int,
    exercise_data: ExerciseUpdate,
    current_user: Annotated[User, Depends(get_current_user_from_token)],
    exercise_service: ExerciseServiceDep,
) -> ExerciseResponse:
    """Update an existing exercise."""
    # Store user ID early to avoid lazy loading in exception handlers
    user_id = current_user.id

    try:
        return await exercise_service.update_user_exercise(
            exercise_id, exercise_data, user_id
        )
    except NotFoundError as e:
        logger.warning(
            f"Exercise {exercise_id} not found for update by user {user_id}: {e}"
        )
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except ValidationError as e:
        logger.warning(
            f"Validation error updating exercise {exercise_id} for user {user_id}: {e}"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e
    except Exception as e:
        logger.error(f"Error updating exercise {exercise_id} for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        ) from e


@router.put(
    "/{exercise_id}",
    response_model=ExerciseResponse,
    summary="Update exercise (PUT)",
    description="Update an existing user exercise. Users can only update their own exercises.",
)
async def update_exercise_put(
    exercise_id: int,
    exercise_data: ExerciseUpdate,
    current_user: Annotated[User, Depends(get_current_user_from_token)],
    exercise_service: ExerciseServiceDep,
) -> ExerciseResponse:
    """Update an existing exercise (PUT method)."""
    return await update_exercise(
        exercise_id, exercise_data, current_user, exercise_service
    )


@router.delete(
    "/{exercise_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete exercise",
    description="Delete a user exercise. Users can only delete their own exercises.",
)
async def delete_exercise(
    exercise_id: int,
    current_user: Annotated[User, Depends(get_current_user_from_token)],
    exercise_service: ExerciseServiceDep,
):
    """Delete an exercise."""
    # Store user ID early to avoid lazy loading in exception handlers
    user_id = current_user.id

    try:
        success = await exercise_service.delete_user_exercise(exercise_id, user_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Exercise not found"
            )
    except NotFoundError as e:
        logger.warning(
            f"Exercise {exercise_id} not found for deletion by user {user_id}: {e}"
        )
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except ValidationError as e:
        logger.warning(
            f"Validation error deleting exercise {exercise_id} for user {user_id}: {e}"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e
    except Exception as e:
        logger.error(f"Error deleting exercise {exercise_id} for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        ) from e
