"""Authentication schemas for request/response models."""

from pydantic import BaseModel, Field


class LogoutResponse(BaseModel):
    """Logout response."""

    message: str = Field(description="Success message")
    logged_out: bool = Field(description="Whether logout was successful")


class UserProfileResponse(BaseModel):
    """User profile response."""

    id: int = Field(description="User ID")
    email: str = Field(description="User email address")
    name: str | None = Field(default=None, description="User display name")
    profile_image_url: str | None = Field(
        default=None, description="URL to user's profile image"
    )
    is_active: bool = Field(description="Whether user account is active")


class TokenValidationResponse(BaseModel):
    """Token validation response."""

    valid: bool = Field(description="Whether the token is valid")
    user_id: int | None = Field(default=None, description="User ID if token is valid")
    email: str | None = Field(default=None, description="User email if token is valid")
    expires_at: str | None = Field(
        default=None, description="Token expiration timestamp"
    )
    token_type: str | None = Field(default=None, description="Type of token")


class SessionInfoResponse(BaseModel):
    """Current session information."""

    authenticated: bool = Field(description="Whether user is authenticated")
    user: UserProfileResponse | None = Field(
        default=None, description="User profile if authenticated"
    )
    session_expires_at: str | None = Field(
        default=None, description="When the session expires"
    )
    permissions: list[str] = Field(default_factory=list, description="User permissions")


class NextAuthUserResponse(BaseModel):
    """User response in NextAuth.js format."""

    id: int = Field(description="User ID")
    email: str = Field(description="User email address")
    name: str | None = Field(default=None, description="User display name")
    image: str | None = Field(default=None, description="URL to user's profile image")


class AuthTokenRequest(BaseModel):
    """Auth.js token verification request."""

    access_token: str = Field(description="Google OAuth access token from Auth.js")


class AuthTokenResponse(BaseModel):
    """Auth.js token verification response."""

    user: NextAuthUserResponse = Field(description="User information")
    session_token: str = Field(description="Backend session token for API access")
