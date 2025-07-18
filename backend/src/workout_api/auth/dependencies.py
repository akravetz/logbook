"""Authentication dependencies for FastAPI dependency injection."""

import logging
from functools import lru_cache
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.config import Settings, get_settings
from ..core.database import get_session
from ..shared.exceptions import AuthenticationError
from ..users.models import User
from ..users.repository import UserRepository
from .google_verification import GoogleTokenVerifier
from .jwt import JWTManager, TokenData
from .service import AuthService

logger = logging.getLogger("workout_api.auth.dependencies")

# HTTP Bearer token scheme
bearer_scheme = HTTPBearer(auto_error=False)
required_bearer_scheme = HTTPBearer(auto_error=True)


@lru_cache
def get_jwt_manager(settings: Annotated[Settings, Depends(get_settings)]) -> JWTManager:
    """Get JWT manager instance."""
    return JWTManager(settings)


@lru_cache
def get_google_verifier(
    settings: Annotated[Settings, Depends(get_settings)],
) -> GoogleTokenVerifier:
    """Get Google token verifier instance."""
    return GoogleTokenVerifier(settings)


def get_auth_service_dependency(
    session: Annotated[AsyncSession, Depends(get_session)],
    jwt_manager: Annotated[JWTManager, Depends(get_jwt_manager)],
    google_verifier: Annotated[GoogleTokenVerifier, Depends(get_google_verifier)],
) -> AuthService:
    """Get AuthService dependency for dependency injection."""
    user_repository = UserRepository(session)
    return AuthService(session, jwt_manager, user_repository, google_verifier)


async def get_current_user_from_token(
    credentials: Annotated[
        HTTPAuthorizationCredentials, Depends(required_bearer_scheme)
    ],
    session: Annotated[AsyncSession, Depends(get_session)],
    jwt_manager: Annotated[JWTManager, Depends(get_jwt_manager)],
) -> User:
    """Get current user from JWT token (required authentication)."""
    try:
        # Verify the token
        token_data: TokenData = jwt_manager.verify_token(
            credentials.credentials, "access"
        )

        # Get user from database using the repository pattern
        user_repo = UserRepository(session)
        user = await user_repo.get_by_id(token_data.user_id)

        if not user:
            logger.warning(f"User {token_data.user_id} not found in database")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not user.is_active:
            logger.warning(f"Inactive user {token_data.user_id} attempted access")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Inactive user",
                headers={"WWW-Authenticate": "Bearer"},
            )

        logger.debug(f"Authenticated user: {user.email_address}")
        return user

    except AuthenticationError as e:
        logger.warning(f"Authentication failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        ) from e
    except Exception as e:
        logger.error(f"Unexpected authentication error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e


async def get_current_user_optional(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    session: Annotated[AsyncSession, Depends(get_session)],
    jwt_manager: Annotated[JWTManager, Depends(get_jwt_manager)],
) -> User | None:
    """Get current user from JWT token (optional authentication)."""
    if not credentials:
        return None

    try:
        # Verify the token
        token_data: TokenData = jwt_manager.verify_token(
            credentials.credentials, "access"
        )

        # Get user from database using the repository pattern
        user_repo = UserRepository(session)
        user = await user_repo.get_by_id(token_data.user_id)

        if not user or not user.is_active:
            return None

        logger.debug(f"Optionally authenticated user: {user.email_address}")
        return user

    except AuthenticationError:
        # For optional auth, we just return None on auth failure
        return None
    except Exception as e:
        logger.error(f"Unexpected error during optional authentication: {e}")
        return None


async def get_current_admin_user(
    current_user: Annotated[User, Depends(get_current_user_from_token)],
) -> User:
    """Get current user and verify admin privileges."""
    if not current_user.is_admin:
        logger.warning(f"Non-admin user {current_user.id} attempted admin access")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )

    logger.debug(f"Authenticated admin user: {current_user.email_address}")
    return current_user


def verify_token_only(
    credentials: Annotated[
        HTTPAuthorizationCredentials, Depends(required_bearer_scheme)
    ],
    jwt_manager: Annotated[JWTManager, Depends(get_jwt_manager)],
) -> TokenData:
    """Verify JWT token and return token data only (no user lookup)."""
    try:
        # Verify the token and return token data
        token_data = jwt_manager.verify_token(credentials.credentials, "access")
        return token_data
    except AuthenticationError as e:
        logger.warning(f"Token verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e


# Type aliases for dependency injection
CurrentUser = Annotated[User, Depends(get_current_user_from_token)]
OptionalUser = Annotated[User | None, Depends(get_current_user_optional)]
AdminUser = Annotated[User, Depends(get_current_admin_user)]
TokenOnly = Annotated[TokenData, Depends(verify_token_only)]

# Export JWT manager dependency for use in other modules
JWTManagerDep = Annotated[JWTManager, Depends(get_jwt_manager)]
AuthServiceDep = Annotated[AuthService, Depends(get_auth_service_dependency)]
