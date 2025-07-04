"""Google OAuth token verification using Google's tokeninfo API."""

import logging

import httpx
from pydantic import BaseModel, EmailStr, Field, ValidationError

from ..core.config import Settings
from ..shared.exceptions import AuthenticationError

logger = logging.getLogger("workout_api.auth.google_verification")


class GoogleTokenInfo(BaseModel):
    """Google token information from tokeninfo API."""

    email: EmailStr = Field(description="User's verified email address")
    name: str | None = Field(default=None, description="User's display name")
    picture: str | None = Field(default=None, description="User's profile picture URL")
    user_id: str = Field(description="Google user ID")
    email_verified: bool = Field(default=True, description="Whether email is verified")
    audience: str = Field(description="OAuth client ID that the token was issued for")
    expires_in: int = Field(description="Seconds until token expires")


class GoogleTokenVerifier:
    """Verifies Google OAuth tokens using Google's tokeninfo API."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.tokeninfo_url = "https://www.googleapis.com/oauth2/v1/tokeninfo"

    async def verify_access_token(self, access_token: str) -> GoogleTokenInfo:
        """Verify Google access token using Google's tokeninfo API.

        Args:
            access_token: Google OAuth access token to verify

        Returns:
            GoogleTokenInfo: Verified token information

        Raises:
            AuthenticationError: If token is invalid or verification fails
        """
        try:
            logger.debug("Verifying Google access token with Google's tokeninfo API")

            # Call Google's tokeninfo API directly with httpx
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    self.tokeninfo_url,
                    params={"access_token": access_token},
                    timeout=10.0,
                )

            if response.status_code != 200:
                logger.warning(f"Google tokeninfo API returned {response.status_code}")
                raise AuthenticationError("Invalid Google access token")

            token_data = response.json()

            # Validate that the token was issued for our client
            if token_data.get("audience") != self.settings.google_client_id:
                logger.warning(
                    f"Token audience mismatch: expected {self.settings.google_client_id}, "
                    f"got {token_data.get('audience')}"
                )
                raise AuthenticationError("Token not issued for this application")

            # Create validated token info
            try:
                token_info = GoogleTokenInfo.model_validate(token_data)
            except ValidationError as e:
                logger.error(f"Invalid Google token response format: {e}")
                raise AuthenticationError("Invalid Google token response format") from e

            logger.info(
                f"Successfully verified Google token for user: {token_info.email}"
            )
            return token_info

        except httpx.TimeoutException as e:
            logger.error(f"Timeout verifying Google token: {e}")
            raise AuthenticationError("Google token verification timeout") from e
        except httpx.RequestError as e:
            logger.error(f"Network error verifying Google token: {e}")
            raise AuthenticationError("Google token verification network error") from e
        except KeyError as e:
            logger.error(f"Missing required field in Google token response: {e}")
            raise AuthenticationError("Invalid Google token response format") from e
        except AuthenticationError:
            # Re-raise authentication errors
            raise
        except Exception as e:
            logger.error(f"Unexpected error verifying Google token: {e}")
            raise AuthenticationError("Google token verification failed") from e
