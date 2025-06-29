"""Authentication router with JWT endpoints for NextAuth.js integration."""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.config import get_settings
from ..core.database import get_session
from ..shared.exceptions import AuthenticationError
from .dependencies import CurrentUser, JWTManagerDep, TokenOnly
from .schemas import (
    LogoutResponse,
    NextAuthGoogleUserRequest,
    NextAuthVerificationResponse,
    SessionInfoResponse,
    TokenRefreshRequest,
    TokenRefreshResponse,
    TokenValidationResponse,
)

logger = logging.getLogger("workout_api.auth.router")
router = APIRouter()


@router.post(
    "/refresh",
    response_model=TokenRefreshResponse,
    summary="Refresh access token",
    description="Use refresh token to get new access token",
    responses={
        401: {"description": "Invalid refresh token"},
    },
)
async def refresh_token(
    refresh_request: TokenRefreshRequest,
    jwt_manager: JWTManagerDep,
) -> TokenRefreshResponse:
    """Refresh JWT access token using refresh token."""
    try:
        # Verify refresh token and get new access token
        new_access_token = jwt_manager.refresh_access_token(
            refresh_request.refresh_token
        )

        settings = get_settings()
        logger.info("Access token refreshed successfully")

        return TokenRefreshResponse(
            access_token=new_access_token,
            expires_in=settings.access_token_expire_minutes * 60,
        )

    except AuthenticationError as e:
        logger.warning(f"Token refresh failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed",
        ) from e


@router.post(
    "/logout",
    response_model=LogoutResponse,
    summary="Logout user",
    description="Logout current user (client-side token invalidation)",
)
async def logout(
    current_user: CurrentUser,
) -> LogoutResponse:
    """Logout user - invalidate tokens on client side."""
    logger.info(f"User logged out: {current_user.email_address}")
    return LogoutResponse(
        message="Successfully logged out. Please remove tokens from client storage.",
        logged_out=True,
    )


@router.get(
    "/me",
    response_model=SessionInfoResponse,
    summary="Get current session info",
    description="Get information about the current authenticated session",
)
async def get_session_info(
    current_user: CurrentUser,
    token_data: TokenOnly,
) -> SessionInfoResponse:
    """Get current authenticated session information."""
    from .schemas import UserProfileResponse

    user_profile = UserProfileResponse(
        id=current_user.id,
        email_address=current_user.email_address,
        google_id=current_user.google_id,
        name=current_user.name,
        profile_image_url=current_user.profile_image_url,
        is_active=current_user.is_active,
        is_admin=current_user.is_admin,
    )

    # Determine permissions
    permissions = ["user"]
    if current_user.is_admin:
        permissions.append("admin")

    return SessionInfoResponse(
        authenticated=True,
        user=user_profile,
        session_expires_at=token_data.expires_at.isoformat(),
        permissions=permissions,
    )


@router.get(
    "/validate",
    response_model=TokenValidationResponse,
    summary="Validate token",
    description="Validate JWT token and return token information",
)
async def validate_token(
    token_data: TokenOnly,
) -> TokenValidationResponse:
    """Validate JWT token and return basic token information."""
    return TokenValidationResponse(
        valid=True,
        user_id=token_data.user_id,
        email=token_data.email,
        expires_at=token_data.expires_at.isoformat(),
        token_type="access",
    )


# NextAuth.js Integration Endpoints


@router.post(
    "/verify-google-user",
    response_model=NextAuthVerificationResponse,
    summary="Verify Google user for NextAuth",
    description="Create or update user from Google OAuth data via NextAuth.js",
    responses={
        401: {"description": "Authentication failed"},
        422: {"description": "Validation Error"},
    },
)
async def verify_google_user(
    request: NextAuthGoogleUserRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
    jwt_manager: JWTManagerDep,
) -> NextAuthVerificationResponse:
    """Verify and create/update user from Google OAuth data via NextAuth.js."""
    try:
        from .schemas import NextAuthTokenResponse, NextAuthUserResponse
        from .service import get_auth_service

        # Convert NextAuth request to internal format
        google_user_info = request.to_google_user_info()

        # Use existing authentication service
        auth_service = get_auth_service(session, jwt_manager)
        user, jwt_tokens = await auth_service.authenticate_with_google(google_user_info)

        # Return properly typed response
        return NextAuthVerificationResponse(
            user=NextAuthUserResponse(
                id=user.id,
                email=user.email_address,
                name=user.name,
                image=user.profile_image_url,
            ),
            tokens=NextAuthTokenResponse(
                access_token=jwt_tokens.access_token,
                refresh_token=jwt_tokens.refresh_token,
                expires_in=jwt_tokens.expires_in,
            ),
        )

    except AuthenticationError as e:
        logger.warning(f"Google user verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.error(f"Google user verification error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="User verification failed",
        ) from e
