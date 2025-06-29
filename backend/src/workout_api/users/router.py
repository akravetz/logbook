"""User API endpoints."""

import logging
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import JSONResponse

from ..auth.dependencies import CurrentUser
from ..shared.exceptions import NotFoundError, ValidationError
from .dependencies import UserServiceDep
from .schemas import UserProfileUpdate, UserResponse, UserStatsResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/users", tags=["users"])


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user profile",
    description="Retrieve the authenticated user's profile information.",
)
async def get_current_user_profile(
    current_user: CurrentUser,
    user_service: UserServiceDep,
) -> UserResponse:
    """Get current user profile."""
    # Store user ID early to avoid accessing it in exception handlers
    user_id = current_user.id
    try:
        user = await user_service.get_user_profile(user_id)
        return user
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except Exception as e:
        logger.error(f"Error getting user profile {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        ) from e


@router.patch(
    "/me",
    response_model=UserResponse,
    summary="Update current user profile",
    description="Update the authenticated user's profile information.",
)
async def update_current_user_profile(
    update_data: UserProfileUpdate,
    current_user: CurrentUser,
    user_service: UserServiceDep,
) -> UserResponse:
    """Update current user profile."""
    # Store user ID early to avoid accessing it in exception handlers
    user_id = current_user.id
    try:
        updated_user = await user_service.update_user_profile(user_id, update_data)
        return updated_user
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)
        ) from e
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except Exception as e:
        logger.error(f"Error updating user profile {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        ) from e


@router.get(
    "/me/stats",
    response_model=UserStatsResponse,
    summary="Get user workout statistics",
    description="Retrieve workout statistics for the authenticated user.",
)
async def get_user_statistics(
    current_user: CurrentUser,
    user_service: UserServiceDep,
    start_date: datetime | None = Query(
        None, description="Start date for statistics calculation (ISO format)"
    ),
    end_date: datetime | None = Query(
        None, description="End date for statistics calculation (ISO format)"
    ),
) -> UserStatsResponse:
    """Get user workout statistics."""
    # Store user ID early to avoid accessing it in exception handlers
    user_id = current_user.id
    try:
        # Validate date range
        if start_date and end_date and start_date > end_date:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Start date must be before end date",
            )

        stats = await user_service.get_user_statistics(
            user_id, start_date=start_date, end_date=end_date
        )
        return stats
    except HTTPException:
        # Re-raise HTTPExceptions (like our date validation) without logging
        raise
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except Exception as e:
        logger.error(f"Error getting user statistics {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        ) from e


@router.delete(
    "/me",
    summary="Deactivate user account",
    description="Deactivate the authenticated user's account (soft delete).",
)
async def deactivate_current_user(
    current_user: CurrentUser,
    user_service: UserServiceDep,
) -> JSONResponse:
    """Deactivate current user account."""
    # Store user ID early to avoid accessing it in exception handlers
    user_id = current_user.id
    try:
        success = await user_service.deactivate_user(user_id)
        if success:
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={"message": "Account deactivated successfully"},
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )
    except Exception as e:
        logger.error(f"Error deactivating user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        ) from e
