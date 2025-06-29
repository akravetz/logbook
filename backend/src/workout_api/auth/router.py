"""Authentication router with OAuth and JWT endpoints."""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.config import get_settings
from ..core.database import get_session
from ..shared.exceptions import AuthenticationError
from .dependencies import CurrentUser, GoogleOAuthDep, JWTManagerDep, TokenOnly
from .schemas import (
    AuthenticationResponse,
    AuthErrorResponse,
    LogoutResponse,
    OAuthInitiateResponse,
    SessionInfoResponse,
    TokenRefreshRequest,
    TokenRefreshResponse,
    TokenValidationResponse,
    UserProfileResponse,
)
from .service import get_auth_service

logger = logging.getLogger("workout_api.auth.router")
router = APIRouter()


@router.post(
    "/google",
    response_model=OAuthInitiateResponse,
    summary="Initiate Google OAuth flow",
    description="Start Google OAuth authentication process and return authorization URL",
)
async def initiate_google_oauth(
    redirect_url: str | None = Query(  # noqa: ARG001
        default=None, description="Post-auth redirect URL"
    ),
    google_oauth: GoogleOAuthDep = None,
) -> OAuthInitiateResponse:
    """Initiate Google OAuth 2.0 authentication flow."""
    try:
        # Generate OAuth authorization URL with state
        authorization_url, state = google_oauth.generate_authorization_url()

        logger.info("OAuth flow initiated")
        return OAuthInitiateResponse(
            authorization_url=authorization_url,
            state=state,
        )

    except Exception as e:
        logger.error(f"Failed to initiate OAuth: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initiate authentication",
        ) from e


@router.get(
    "/google/callback",
    response_model=AuthenticationResponse,
    summary="Handle Google OAuth callback",
    description="Process Google OAuth callback and return user with JWT tokens",
    responses={
        400: {
            "model": AuthErrorResponse,
            "description": "OAuth error or invalid state",
        },
        401: {"model": AuthErrorResponse, "description": "Authentication failed"},
    },
)
async def google_oauth_callback(
    code: str = Query(description="Authorization code from Google"),
    state: str = Query(description="OAuth state parameter"),
    error: str | None = Query(default=None, description="OAuth error"),
    error_description: str | None = Query(
        default=None, description="OAuth error description"
    ),
    session: Annotated[AsyncSession, Depends(get_session)] = None,
    jwt_manager: JWTManagerDep = None,
    google_oauth: GoogleOAuthDep = None,
) -> AuthenticationResponse:
    """Handle Google OAuth 2.0 callback and authenticate user."""
    try:
        # Check for OAuth errors
        if error:
            logger.warning(f"OAuth error: {error} - {error_description}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"OAuth error: {error_description or error}",
            )

        # Handle OAuth callback
        google_tokens = await google_oauth.exchange_code_for_tokens(code, state)
        google_user_info = await google_oauth.get_user_info(
            google_tokens["access_token"]
        )

        # Authenticate or create user
        auth_service = get_auth_service(session, jwt_manager)
        user, jwt_tokens = await auth_service.authenticate_with_google(google_user_info)

        # Create response
        user_profile = UserProfileResponse.model_validate(user)
        token_response = {
            "access_token": jwt_tokens.access_token,
            "refresh_token": jwt_tokens.refresh_token,
            "token_type": jwt_tokens.token_type,
            "expires_in": jwt_tokens.expires_in,
        }

        logger.info(f"User authenticated successfully: {user.email_address}")
        return AuthenticationResponse(
            user=user_profile,
            tokens=token_response,
        )

    except AuthenticationError as e:
        logger.warning(f"Authentication failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.error(f"OAuth callback error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication failed",
        ) from e


@router.post(
    "/refresh",
    response_model=TokenRefreshResponse,
    summary="Refresh access token",
    description="Use refresh token to get new access token",
    responses={
        401: {"model": AuthErrorResponse, "description": "Invalid refresh token"},
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
    # Note: In a production system, you might want to:
    # 1. Maintain a token blacklist in Redis
    # 2. Store active sessions in database
    # 3. Implement proper server-side token invalidation

    logger.info(f"User logged out: {current_user.email_address}")
    return LogoutResponse(
        message="Successfully logged out. Please remove tokens from client storage.",
        logged_out=True,
    )


@router.get(
    "/me",
    response_model=SessionInfoResponse,
    summary="Get current session info",
    description="Get current user session information",
)
async def get_session_info(
    current_user: CurrentUser,
    token_data: TokenOnly,
) -> SessionInfoResponse:
    """Get current session information."""
    try:
        user_profile = UserProfileResponse.model_validate(current_user)

        permissions = ["user"]
        if current_user.is_admin:
            permissions.append("admin")

        return SessionInfoResponse(
            authenticated=True,
            user=user_profile,
            session_expires_at=token_data.expires_at.isoformat(),
            permissions=permissions,
        )

    except Exception as e:
        logger.error(f"Session info error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get session information",
        ) from e


@router.get(
    "/validate",
    response_model=TokenValidationResponse,
    summary="Validate token",
    description="Validate JWT token and return token information",
)
async def validate_token(
    token_data: TokenOnly,
) -> TokenValidationResponse:
    """Validate JWT token and return token information."""
    try:
        return TokenValidationResponse(
            valid=True,
            user_id=token_data.user_id,
            email=token_data.email,
            expires_at=token_data.expires_at.isoformat(),
            token_type=token_data.token_type,
        )

    except Exception as e:
        logger.error(f"Token validation error: {e}")
        return TokenValidationResponse(valid=False)


# Health check for auth system
@router.get(
    "/health",
    summary="Authentication system health",
    description="Check if authentication system is working",
)
async def auth_health_check():
    """Check authentication system health."""
    try:
        settings = get_settings()

        # Basic configuration checks
        config_ok = bool(
            settings.google_client_id
            and settings.google_client_secret
            and settings.jwt_secret_key
        )

        return {
            "status": "healthy" if config_ok else "unhealthy",
            "auth_system": "operational" if config_ok else "configuration_error",
            "google_oauth": "configured"
            if settings.google_client_id
            else "not_configured",
            "jwt": "configured" if settings.jwt_secret_key else "not_configured",
        }

    except Exception as e:
        logger.error(f"Auth health check failed: {e}")
        return {
            "status": "unhealthy",
            "auth_system": "error",
            "error": str(e),
        }
