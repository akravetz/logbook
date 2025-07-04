"""Authentication router with JWT endpoints for NextAuth.js integration."""

import logging

from fastapi import APIRouter, HTTPException, status

from ..shared.exceptions import AuthenticationError
from .dependencies import AuthServiceDep, CurrentUser, TokenOnly
from .schemas import (
    AuthTokenRequest,
    AuthTokenResponse,
    LogoutResponse,
    NextAuthUserResponse,
    SessionInfoResponse,
    TokenValidationResponse,
    UserProfileResponse,
)

logger = logging.getLogger("workout_api.auth.router")
router = APIRouter()


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
    user_profile = UserProfileResponse(
        id=current_user.id,
        email=current_user.email_address,
        name=current_user.name,
        profile_image_url=current_user.profile_image_url,
        is_active=current_user.is_active,
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


# Auth.js Secure Integration Endpoints


@router.post(
    "/verify-token",
    response_model=AuthTokenResponse,
    summary="Verify Auth.js Google token",
    description="Securely verify Google OAuth token from Auth.js and return session token",
    responses={
        401: {"description": "Invalid or expired Google token"},
        422: {"description": "Validation Error"},
    },
)
async def verify_auth_token(
    request: AuthTokenRequest,
    auth_service: AuthServiceDep,
) -> AuthTokenResponse:
    """Securely verify Google OAuth token from Auth.js using Google's tokeninfo API."""
    try:
        # Use secure Google token verification
        (
            user,
            session_token,
        ) = await auth_service.authenticate_with_verified_google_token(
            request.access_token
        )

        # Return user info and session token
        return AuthTokenResponse(
            user=NextAuthUserResponse(
                id=user.id,
                email=user.email_address,
                name=user.name,
                image=user.profile_image_url,
            ),
            session_token=session_token,
        )

    except AuthenticationError as e:
        logger.warning(f"Google token verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.error(f"Google token verification error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token verification failed",
        ) from e
