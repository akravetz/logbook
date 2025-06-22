"""User database models."""

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from ..shared.base_model import BaseModel


class User(BaseModel):
    """User model for storing user profile information."""

    __tablename__ = "users"

    email_address: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, doc="User's email address from Google"
    )
    google_id: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, doc="Google OAuth user ID"
    )
    name: Mapped[str] = mapped_column(String(255), doc="User's display name")
    profile_image_url: Mapped[str | None] = mapped_column(
        String(500), doc="URL to user's profile image"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, doc="Whether the user account is active"
    )
    is_admin: Mapped[bool] = mapped_column(
        Boolean, default=False, doc="Whether the user has admin privileges"
    )

    def __repr__(self) -> str:
        """String representation of the User."""
        return f"<User(id={self.id}, email={self.email_address})>"
