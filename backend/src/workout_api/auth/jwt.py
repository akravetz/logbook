"""JWT token management for authentication."""

import logging
from datetime import UTC, datetime, timedelta
from typing import Any, Protocol

from jose import JWTError, jwt
from pydantic import BaseModel, Field

from ..core.config import Settings
from ..shared.exceptions import AuthenticationError

logger = logging.getLogger("workout_api.auth.jwt")


class TokenData(BaseModel):
    """Token payload data structure."""

    user_id: int = Field(description="User ID from database")
    email: str = Field(description="User email address")
    token_type: str = Field(description="Type of token (access/refresh)")
    issued_at: datetime = Field(description="Token issued timestamp")
    expires_at: datetime = Field(description="Token expiration timestamp")


class TokenPair(BaseModel):
    """Access and refresh token pair."""

    access_token: str = Field(description="JWT access token")
    refresh_token: str = Field(description="JWT refresh token")
    token_type: str = Field(default="Bearer", description="Token type")
    expires_in: int = Field(description="Access token expiration in seconds")
    expires_at: str = Field(
        description="Access token expiration timestamp in ISO format"
    )


class TimeProvider(Protocol):
    """Protocol for time provider to enable testing."""

    def now(self) -> datetime:
        """Get current time."""
        ...


class DefaultTimeProvider:
    """Default time provider using system time."""

    def now(self) -> datetime:
        """Get current time."""
        return datetime.now(UTC)


class JWTManager:
    """JWT token management class."""

    def __init__(self, settings: Settings, time_provider: TimeProvider | None = None):
        self.settings = settings
        self.secret_key = settings.jwt_secret_key
        self.algorithm = settings.jwt_algorithm
        self.access_token_expire_minutes = settings.access_token_expire_minutes
        self.refresh_token_expire_days = settings.refresh_token_expire_days
        self.time_provider = time_provider or DefaultTimeProvider()

    def create_access_token(self, user_id: int, email: str) -> str:
        """Create a new access token."""
        now = self.time_provider.now()
        expires_delta = timedelta(minutes=self.access_token_expire_minutes)
        expires_at = now + expires_delta

        payload = {
            "sub": str(user_id),  # Subject (user ID)
            "email": email,
            "token_type": "access",
            "iat": now,  # Issued at
            "exp": expires_at,  # Expiration time
            "jti": f"access_{user_id}_{int(now.timestamp())}",  # JWT ID
        }

        try:
            token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
            logger.debug(f"Created access token for user {user_id}")
            return token
        except Exception as e:
            logger.error(f"Failed to create access token for user {user_id}: {e}")
            raise AuthenticationError("Failed to create access token") from e

    def create_refresh_token(self, user_id: int, email: str) -> str:
        """Create a new refresh token."""
        now = self.time_provider.now()
        expires_delta = timedelta(days=self.refresh_token_expire_days)
        expires_at = now + expires_delta

        payload = {
            "sub": str(user_id),
            "email": email,
            "token_type": "refresh",
            "iat": now,
            "exp": expires_at,
            "jti": f"refresh_{user_id}_{int(now.timestamp())}",
        }

        try:
            token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
            logger.debug(f"Created refresh token for user {user_id}")
            return token
        except Exception as e:
            logger.error(f"Failed to create refresh token for user {user_id}: {e}")
            raise AuthenticationError("Failed to create refresh token") from e

    def create_token_pair(self, user_id: int, email: str) -> TokenPair:
        """Create both access and refresh tokens."""
        access_token = self.create_access_token(user_id, email)
        refresh_token = self.create_refresh_token(user_id, email)

        # Calculate expiration timestamp
        expires_at = self.time_provider.now() + timedelta(
            minutes=self.access_token_expire_minutes
        )

        return TokenPair(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=self.access_token_expire_minutes * 60,  # Convert to seconds
            expires_at=expires_at.isoformat(),
        )

    def verify_token(self, token: str, expected_type: str = "access") -> TokenData:
        """Verify and decode a JWT token."""
        try:
            # Decode token without verifying expiration (we'll check it manually)
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
                options={"verify_exp": False},  # We'll check expiration manually
            )

            # Extract token data
            user_id = int(payload.get("sub"))
            email = payload.get("email")
            token_type = payload.get("token_type")
            issued_at = datetime.fromtimestamp(payload.get("iat"), tz=UTC)
            expires_at = datetime.fromtimestamp(payload.get("exp"), tz=UTC)

            # Validate token type
            if token_type != expected_type:
                logger.warning(
                    f"Token type mismatch: expected {expected_type}, got {token_type}"
                )
                raise AuthenticationError("Invalid token type")

            # Check if token has expired using our time provider
            if expires_at < self.time_provider.now():
                logger.warning(f"Token expired for user {user_id}")
                raise AuthenticationError("Token has expired")

            token_data = TokenData(
                user_id=user_id,
                email=email,
                token_type=token_type,
                issued_at=issued_at,
                expires_at=expires_at,
            )

            logger.debug(f"Successfully verified {token_type} token for user {user_id}")
            return token_data

        except JWTError as e:
            logger.warning(f"JWT validation error: {e}")
            raise AuthenticationError("Invalid token") from e
        except ValueError as e:
            logger.warning(f"Token payload validation error: {e}")
            raise AuthenticationError("Invalid token payload") from e
        except AuthenticationError:
            raise  # Re-raise our authentication errors
        except Exception as e:
            logger.error(f"Unexpected error during token verification: {e}")
            raise AuthenticationError("Token verification failed") from e

    def refresh_access_token(self, refresh_token: str) -> str:
        """Create a new access token from a valid refresh token."""
        # Verify the refresh token
        token_data = self.verify_token(refresh_token, expected_type="refresh")

        # Create new access token
        new_access_token = self.create_access_token(
            token_data.user_id, token_data.email
        )

        logger.info(f"Refreshed access token for user {token_data.user_id}")
        return new_access_token

    def refresh_token_pair(self, refresh_token: str) -> TokenPair:
        """Create new token pair from a valid refresh token.

        This implements token rotation - the old refresh token should be
        invalidated after this call.
        """
        # Verify the refresh token
        token_data = self.verify_token(refresh_token, expected_type="refresh")

        # Create new token pair
        token_pair = self.create_token_pair(token_data.user_id, token_data.email)

        logger.info(f"Refreshed token pair for user {token_data.user_id}")
        return token_pair

    def get_token_info(self, token: str) -> dict[str, Any]:
        """Get token information without full validation (for debugging)."""
        try:
            # Decode without verification to get info
            payload = jwt.get_unverified_claims(token)
            return {
                "user_id": payload.get("sub"),
                "email": payload.get("email"),
                "token_type": payload.get("token_type"),
                "issued_at": payload.get("iat"),
                "expires_at": payload.get("exp"),
                "jwt_id": payload.get("jti"),
            }
        except Exception as e:
            logger.error(f"Failed to get token info: {e}")
            return {}
