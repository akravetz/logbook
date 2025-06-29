"""Google OAuth 2.0 integration for user authentication."""

import logging
import secrets
from typing import Any
from urllib.parse import urlencode

import httpx
from authlib.integrations.starlette_client import OAuth

from ..core.config import Settings
from ..shared.exceptions import AuthenticationError

logger = logging.getLogger("workout_api.auth.google")


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


class GoogleOAuthManager:
    """Google OAuth 2.0 flow manager."""

    def __init__(
        self, settings: Settings, http_client: httpx.AsyncClient | None = None
    ):
        self.settings = settings
        self.client_id = settings.google_client_id
        self.client_secret = settings.google_client_secret
        self.redirect_uri = settings.google_redirect_uri
        self.discovery_url = settings.google_discovery_url
        self.http_client = http_client

        # OAuth scopes
        self.scopes = ["openid", "email", "profile"]

        # Initialize OAuth client
        self.oauth = OAuth()
        self.oauth.register(
            name="google",
            client_id=self.client_id,
            client_secret=self.client_secret,
            server_metadata_url=self.discovery_url,
            client_kwargs={"scope": " ".join(self.scopes)},
        )

    def generate_authorization_url(self, state: str | None = None) -> tuple[str, str]:
        """Generate Google OAuth authorization URL with state parameter."""
        if not state:
            state = secrets.token_urlsafe(32)

        # Build authorization URL manually for full control
        base_url = "https://accounts.google.com/o/oauth2/v2/auth"
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "scope": " ".join(self.scopes),
            "response_type": "code",
            "state": state,
            "access_type": "offline",  # Request refresh token
            "prompt": "consent",  # Force consent screen for refresh token
        }

        authorization_url = f"{base_url}?{urlencode(params)}"

        logger.info(f"Generated OAuth authorization URL with state: {state[:8]}...")
        return authorization_url, state

    async def exchange_code_for_tokens(self, code: str, state: str) -> dict[str, Any]:  # noqa: ARG002
        """Exchange authorization code for access tokens."""
        token_url = "https://oauth2.googleapis.com/token"

        token_data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": self.redirect_uri,
        }

        try:
            # Use injected client if available, otherwise create a new one
            if self.http_client:
                response = await self.http_client.post(
                    token_url,
                    data=token_data,
                    headers={"Accept": "application/json"},
                    timeout=30.0,
                )
            else:
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        token_url,
                        data=token_data,
                        headers={"Accept": "application/json"},
                        timeout=30.0,
                    )

            if response.status_code != 200:
                logger.error(
                    f"Token exchange failed: {response.status_code} - {response.text}"
                )
                raise GoogleOAuthError(
                    "Failed to exchange authorization code for tokens"
                )

            tokens = response.json()

            # Validate token response
            if "access_token" not in tokens:
                logger.error("Access token not found in response")
                raise GoogleOAuthError("Invalid token response from Google")

            logger.info("Successfully exchanged authorization code for tokens")
            return tokens

        except httpx.RequestError as e:
            logger.error(f"Network error during token exchange: {e}")
            raise GoogleOAuthError("Network error during authentication") from e
        except GoogleOAuthError:
            raise  # Re-raise our custom errors
        except Exception as e:
            logger.error(f"Unexpected error during token exchange: {e}")
            raise GoogleOAuthError("Authentication failed") from e

    async def get_user_info(self, access_token: str) -> GoogleUserInfo:
        """Get user information from Google using access token."""
        userinfo_url = "https://www.googleapis.com/oauth2/v2/userinfo"

        headers = {"Authorization": f"Bearer {access_token}"}

        try:
            # Use injected client if available, otherwise create a new one
            if self.http_client:
                response = await self.http_client.get(
                    userinfo_url,
                    headers=headers,
                    timeout=30.0,
                )
            else:
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        userinfo_url,
                        headers=headers,
                        timeout=30.0,
                    )

            if response.status_code != 200:
                logger.error(
                    f"User info request failed: {response.status_code} - {response.text}"
                )
                raise GoogleOAuthError("Failed to retrieve user information")

            user_data = response.json()
            user_info = GoogleUserInfo(user_data)

            # Validate user info
            if not user_info.is_valid():
                logger.error(f"Invalid user info received: {user_info.to_dict()}")
                raise GoogleOAuthError("Invalid user information from Google")

            logger.info(f"Successfully retrieved user info for {user_info.email}")
            return user_info

        except httpx.RequestError as e:
            logger.error(f"Network error during user info retrieval: {e}")
            raise GoogleOAuthError(
                "Network error during user information retrieval"
            ) from e
        except GoogleOAuthError:
            raise  # Re-raise our custom errors
        except Exception as e:
            logger.error(f"Unexpected error during user info retrieval: {e}")
            raise GoogleOAuthError("Failed to retrieve user information") from e

    async def verify_token(self, access_token: str) -> dict[str, Any]:
        """Verify Google access token and return token info."""
        tokeninfo_url = f"https://www.googleapis.com/oauth2/v1/tokeninfo?access_token={access_token}"

        try:
            # Use injected client if available, otherwise create a new one
            if self.http_client:
                response = await self.http_client.get(tokeninfo_url, timeout=30.0)
            else:
                async with httpx.AsyncClient() as client:
                    response = await client.get(tokeninfo_url, timeout=30.0)

            if response.status_code != 200:
                logger.warning(f"Token verification failed: {response.status_code}")
                raise GoogleOAuthError("Invalid access token")

            token_info = response.json()

            # Verify token audience (client_id)
            if token_info.get("audience") != self.client_id:
                logger.warning("Token audience mismatch")
                raise GoogleOAuthError("Token not issued for this application")

            logger.debug("Access token verified successfully")
            return token_info

        except httpx.RequestError as e:
            logger.error(f"Network error during token verification: {e}")
            raise GoogleOAuthError("Network error during token verification") from e
        except GoogleOAuthError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error during token verification: {e}")
            raise GoogleOAuthError("Token verification failed") from e

    def validate_state(self, received_state: str, expected_state: str) -> bool:
        """Validate OAuth state parameter to prevent CSRF attacks."""
        if not received_state or not expected_state:
            logger.warning("Missing state parameter in OAuth callback")
            return False

        if received_state != expected_state:
            logger.warning("OAuth state parameter mismatch")
            return False

        logger.debug("OAuth state parameter validated successfully")
        return True
