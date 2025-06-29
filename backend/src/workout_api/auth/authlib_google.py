"""Authlib-based Google OAuth 2.0 integration for user authentication."""

import logging
from typing import Any

from authlib.integrations.starlette_client import OAuth
from starlette.requests import Request

from ..core.config import Settings
from ..shared.exceptions import AuthenticationError

logger = logging.getLogger("workout_api.auth.authlib_google")


class GoogleOAuthError(AuthenticationError):
    """Specific exception for Google OAuth errors."""

    pass


class GoogleUserInfo:
    """Google user information container."""

    def __init__(self, data: dict[str, Any]):
        # Google userinfo endpoint returns user ID in "id" field, not "sub"
        self.google_id: str = data.get("id", "") or data.get("sub", "")
        self.email: str = data.get("email", "")
        self.name: str = data.get("name", "")
        self.picture: str = data.get("picture", "")
        # Google userinfo endpoint returns email_verified as string, not boolean
        email_verified_raw = data.get("email_verified", False)
        self.email_verified: bool = (
            email_verified_raw
            if isinstance(email_verified_raw, bool)
            else str(email_verified_raw).lower() == "true"
        )
        self.given_name: str = data.get("given_name", "")
        self.family_name: str = data.get("family_name", "")

    def is_valid(self) -> bool:
        """Check if user info contains required fields."""
        # For development, we'll be more lenient with email verification
        # In production, you might want to require email_verified=True
        return bool(self.google_id and self.email)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "google_id": self.google_id,
            "email": self.email,
            "name": self.name,
            "picture": self.picture,
            "email_verified": self.email_verified,
            "given_name": self.given_name,
            "family_name": self.family_name,
        }


class AuthlibGoogleManager:
    """Authlib-based Google OAuth 2.0 flow manager."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.client_id = settings.google_client_id
        self.client_secret = settings.google_client_secret
        self.redirect_uri = settings.google_redirect_uri
        self.discovery_url = settings.google_discovery_url

        # OAuth scopes
        self.scopes = ["openid", "email", "profile"]

        # Initialize OAuth client with Authlib
        self.oauth = OAuth()
        self.oauth.register(
            name="google",
            client_id=self.client_id,
            client_secret=self.client_secret,
            server_metadata_url=self.discovery_url,
            client_kwargs={"scope": " ".join(self.scopes)},
        )

        logger.info("Authlib Google OAuth manager initialized")

    async def authorize_redirect(
        self, request: Request, redirect_uri: str | None = None
    ) -> Any:
        """Generate OAuth authorization redirect response.

        Args:
            request: FastAPI Request object (required for session management)
            redirect_uri: OAuth redirect URI (uses configured URI if None)

        Returns:
            RedirectResponse to Google OAuth authorization endpoint
        """
        try:
            # Use configured redirect URI if none provided
            if redirect_uri is None:
                redirect_uri = self.redirect_uri

            # Generate authorization redirect using Authlib
            # This automatically handles state generation and CSRF protection via sessions
            redirect_response = await self.oauth.google.authorize_redirect(
                request, redirect_uri
            )

            logger.info("Generated OAuth authorization redirect")
            return redirect_response

        except Exception as e:
            logger.error(f"Failed to generate authorization redirect: {e}")
            raise GoogleOAuthError("Failed to initiate OAuth flow") from e

    async def authorize_access_token(self, request: Request) -> dict[str, Any]:
        """Exchange authorization code for access token and retrieve user info.

        Args:
            request: FastAPI Request object (contains OAuth callback parameters)

        Returns:
            Dictionary containing tokens and user info
        """
        try:
            # Exchange code for tokens and get user info in one call
            # This automatically validates state for CSRF protection
            token = await self.oauth.google.authorize_access_token(request)

            if not token:
                logger.error("No token received from OAuth callback")
                raise GoogleOAuthError("Failed to receive access token")

            # Extract user info from token (automatically parsed by Authlib)
            userinfo = token.get("userinfo")
            if not userinfo:
                logger.error("No userinfo found in token response")
                raise GoogleOAuthError("Failed to retrieve user information")

            logger.info("Successfully completed OAuth token exchange")

            # Return both tokens and parsed user info
            return {
                "access_token": token.get("access_token"),
                "refresh_token": token.get("refresh_token"),
                "token_type": token.get("token_type", "Bearer"),
                "expires_in": token.get("expires_in"),
                "userinfo": userinfo,
            }

        except GoogleOAuthError:
            raise  # Re-raise our custom errors
        except Exception as e:
            logger.error(f"OAuth token exchange failed: {e}")
            raise GoogleOAuthError("OAuth authentication failed") from e

    def parse_user_info(self, userinfo_data: dict[str, Any]) -> GoogleUserInfo:
        """Parse user info data into GoogleUserInfo object.

        Args:
            userinfo_data: Raw user info from OAuth token

        Returns:
            GoogleUserInfo object with parsed data
        """
        try:
            user_info = GoogleUserInfo(userinfo_data)

            if not user_info.is_valid():
                logger.error(f"Invalid user info received: {user_info.to_dict()}")
                raise GoogleOAuthError("Invalid user information from Google")

            logger.debug(f"Parsed user info for: {user_info.email}")
            return user_info

        except GoogleOAuthError:
            raise
        except Exception as e:
            logger.error(f"Failed to parse user info: {e}")
            raise GoogleOAuthError("Failed to parse user information") from e
