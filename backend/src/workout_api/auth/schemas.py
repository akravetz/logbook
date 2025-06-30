"""Authentication schemas for request/response models."""

from pydantic import BaseModel, EmailStr, Field, HttpUrl


class OAuthInitiateRequest(BaseModel):
    """Request to initiate OAuth flow."""

    redirect_url: str | None = Field(
        default=None,
        description="Optional redirect URL after successful authentication",
    )


class OAuthInitiateResponse(BaseModel):
    """Response with OAuth authorization URL."""

    authorization_url: HttpUrl = Field(description="Google OAuth authorization URL")
    state: str = Field(description="OAuth state parameter for CSRF protection")


class OAuthCallbackRequest(BaseModel):
    """OAuth callback request parameters."""

    code: str = Field(description="Authorization code from Google")
    state: str = Field(description="OAuth state parameter")
    error: str | None = Field(default=None, description="OAuth error if any")
    error_description: str | None = Field(
        default=None, description="OAuth error description"
    )


class TokenResponse(BaseModel):
    """JWT token response."""

    access_token: str = Field(description="JWT access token")
    refresh_token: str = Field(description="JWT refresh token")
    token_type: str = Field(default="Bearer", description="Token type")
    expires_in: int = Field(description="Access token expiration in seconds")


class TokenRefreshRequest(BaseModel):
    """Token refresh request."""

    refresh_token: str = Field(description="Valid refresh token")


class TokenRefreshResponse(BaseModel):
    """Token refresh response."""

    access_token: str = Field(description="New JWT access token")
    token_type: str = Field(default="Bearer", description="Token type")
    expires_in: int = Field(description="Access token expiration in seconds")


class UserProfileResponse(BaseModel):
    """User profile response."""

    id: int = Field(description="User ID")
    email_address: str = Field(description="User email address")
    google_id: str = Field(description="Google OAuth user ID")
    name: str = Field(description="User display name")
    profile_image_url: str | None = Field(description="URL to user's profile image")
    is_active: bool = Field(description="Whether the user account is active")
    is_admin: bool = Field(description="Whether the user has admin privileges")

    model_config = {"from_attributes": True}


class AuthenticationResponse(BaseModel):
    """Complete authentication response with user and tokens."""

    user: UserProfileResponse = Field(description="User profile information")
    tokens: TokenResponse = Field(description="JWT token pair")


class LogoutResponse(BaseModel):
    """Logout response."""

    message: str = Field(
        default="Successfully logged out", description="Logout message"
    )
    logged_out: bool = Field(default=True, description="Logout status")


class AuthErrorResponse(BaseModel):
    """Authentication error response."""

    error: str = Field(description="Error type")
    error_description: str = Field(description="Detailed error description")
    error_code: str | None = Field(default=None, description="Internal error code")


class TokenValidationResponse(BaseModel):
    """Token validation response."""

    valid: bool = Field(description="Whether the token is valid")
    user_id: int | None = Field(default=None, description="User ID if token is valid")
    email: str | None = Field(default=None, description="User email if token is valid")
    expires_at: str | None = Field(
        default=None, description="Token expiration timestamp"
    )
    token_type: str | None = Field(default=None, description="Type of token")


class GoogleUserInfoResponse(BaseModel):
    """Google user information response."""

    google_id: str = Field(description="Google user ID")
    email: str = Field(description="User email address")
    name: str = Field(description="User display name")
    picture: str | None = Field(description="URL to user's profile picture")
    email_verified: bool = Field(description="Whether email is verified")
    given_name: str | None = Field(description="User's first name")
    family_name: str | None = Field(description="User's last name")


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


class GoogleUserInfo(BaseModel):
    """Google user information from OAuth."""

    email: EmailStr
    name: str | None = None
    picture: str | None = None
    email_verified: bool = True
    google_id: str | None = None

    @classmethod
    def from_nextauth(cls, user_data: dict) -> "GoogleUserInfo":
        """Create from NextAuth.js user data."""
        return cls(
            email=user_data["email"],
            name=user_data.get("name"),
            picture=user_data.get("image"),
            email_verified=user_data.get("email_verified", True),
            google_id=user_data.get(
                "id", user_data["email"]
            ),  # Use email as fallback ID
        )


class NextAuthGoogleUserRequest(BaseModel):
    """NextAuth.js Google user verification request."""

    email: EmailStr = Field(description="User's email address from Google")
    name: str | None = Field(default=None, description="User's display name")
    image: str | None = Field(default=None, description="URL to user's profile image")
    email_verified: bool = Field(
        default=True, description="Whether email is verified by Google"
    )

    def to_google_user_info(self) -> GoogleUserInfo:
        """Convert to internal GoogleUserInfo format."""
        return GoogleUserInfo(
            email=self.email,
            name=self.name,
            picture=self.image,  # Map image -> picture
            email_verified=self.email_verified,
            google_id=None,  # Will be handled by service layer
        )


class NextAuthUserResponse(BaseModel):
    """User data in NextAuth.js expected format."""

    id: int = Field(description="User ID")
    email: str = Field(description="User email address")
    name: str = Field(description="User display name")
    image: str | None = Field(description="URL to user's profile image")


class NextAuthTokenResponse(BaseModel):
    """JWT tokens in NextAuth.js expected format."""

    access_token: str = Field(description="JWT access token")
    refresh_token: str = Field(description="JWT refresh token")
    expires_in: int = Field(description="Access token expiration in seconds")


class NextAuthVerificationResponse(BaseModel):
    """Complete NextAuth.js verification response."""

    user: NextAuthUserResponse = Field(description="User information")
    tokens: NextAuthTokenResponse = Field(description="JWT token pair")


class DevLoginRequest(BaseModel):
    """Development login request - email only."""

    email: EmailStr = Field(description="Email address for development login")


class DevLoginResponse(BaseModel):
    """Development login response."""

    user: NextAuthUserResponse = Field(description="User information")
    tokens: NextAuthTokenResponse = Field(description="JWT token pair")
    message: str = Field(
        default="Development login successful", description="Success message"
    )
