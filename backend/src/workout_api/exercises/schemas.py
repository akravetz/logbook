"""Exercise API schemas."""

from datetime import datetime
from typing import TypeVar

from pydantic import BaseModel, Field, HttpUrl

from .models import ExerciseModality

# Generic type variable for Page items
T = TypeVar("T")


class ExerciseFilters(BaseModel):
    """Filters for exercise search."""

    name: str | None = Field(
        None, description="Filter by exercise name (partial match)"
    )
    body_part: str | None = Field(None, description="Filter by body part")
    modality: ExerciseModality | None = Field(
        None, description="Filter by exercise modality"
    )
    is_user_created: bool | None = Field(
        None, description="Filter by user-created vs system exercises"
    )
    created_by_user_id: int | None = Field(
        None, description="Filter exercises created by specific user"
    )


class ExerciseCreate(BaseModel):
    """Schema for creating a new exercise."""

    name: str = Field(..., min_length=1, max_length=255, description="Exercise name")
    body_part: str = Field(
        ..., min_length=1, max_length=100, description="Primary body part targeted"
    )
    modality: ExerciseModality = Field(..., description="Equipment/modality used")
    picture_url: HttpUrl | None = Field(
        None, description="URL to exercise demonstration image"
    )


class ExerciseUpdate(BaseModel):
    """Schema for updating an existing exercise."""

    name: str | None = Field(
        None, min_length=1, max_length=255, description="Exercise name"
    )
    body_part: str | None = Field(
        None, min_length=1, max_length=100, description="Primary body part targeted"
    )
    modality: ExerciseModality | None = Field(
        None, description="Equipment/modality used"
    )
    picture_url: HttpUrl | None = Field(
        None, description="URL to exercise demonstration image"
    )


class ExerciseResponse(BaseModel):
    """Schema for exercise responses."""

    id: int
    name: str
    body_part: str
    modality: ExerciseModality
    picture_url: str | None = None
    is_user_created: bool
    created_by_user_id: int | None = None
    updated_by_user_id: int | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class Pagination(BaseModel):
    """Pagination parameters."""

    page: int = Field(1, ge=1, description="Page number (1-based)")
    size: int = Field(20, ge=1, le=100, description="Page size (max 100)")

    @property
    def offset(self) -> int:
        """Calculate offset for database queries."""
        return (self.page - 1) * self.size


class Page[T](BaseModel):
    """Paginated response wrapper."""

    items: list[T]
    total: int = Field(..., description="Total number of items")
    page: int = Field(..., description="Current page number")
    size: int = Field(..., description="Page size")
    pages: int = Field(..., description="Total number of pages")

    @classmethod
    def create(cls, items: list[T], total: int, page: int, size: int) -> "Page[T]":
        """Create a paginated response."""
        pages = (total + size - 1) // size  # Ceiling division
        return cls(items=items, total=total, page=page, size=size, pages=pages)
