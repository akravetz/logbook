"""Workout API schemas."""

from datetime import datetime
from typing import TypeVar

from pydantic import BaseModel, Field

# Generic type variable for Page items
T = TypeVar("T")


class WorkoutFilters(BaseModel):
    """Filters for workout search."""

    start_date: datetime | None = Field(
        None, description="Filter workouts created after this date"
    )
    end_date: datetime | None = Field(
        None, description="Filter workouts created before this date"
    )
    finished: bool | None = Field(
        None,
        description="Filter by completion status (true=finished, false=in progress)",
    )


class WorkoutResponse(BaseModel):
    """Schema for workout responses."""

    id: int
    finished_at: datetime | None = None
    created_by_user_id: int
    updated_by_user_id: int
    created_at: datetime
    updated_at: datetime
    exercise_executions: list["ExerciseExecutionResponse"] = []

    model_config = {"from_attributes": True}


class SetCreate(BaseModel):
    """Schema for creating a new set."""

    note_text: str | None = Field(None, description="Optional notes about this set")
    weight: float = Field(..., ge=0, description="Weight used for this set (in pounds)")
    clean_reps: int = Field(
        ..., ge=0, description="Number of clean repetitions completed"
    )
    forced_reps: int = Field(
        0, ge=0, description="Number of forced repetitions completed"
    )


class SetUpdate(BaseModel):
    """Schema for updating an existing set."""

    note_text: str | None = Field(None, description="Optional notes about this set")
    weight: float | None = Field(
        None, ge=0, description="Weight used for this set (in pounds)"
    )
    clean_reps: int | None = Field(
        None, ge=0, description="Number of clean repetitions completed"
    )
    forced_reps: int | None = Field(
        None, ge=0, description="Number of forced repetitions completed"
    )


class SetResponse(BaseModel):
    """Schema for set responses."""

    id: int
    exercise_id: int
    note_text: str | None = None
    weight: float
    clean_reps: int
    forced_reps: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ExerciseExecutionRequest(BaseModel):
    """Schema for creating/updating exercise execution (full replace)."""

    exercise_order: int = Field(
        ..., ge=1, description="Order of this exercise in the workout (1-based)"
    )
    note_text: str | None = Field(
        None, description="Optional notes about this exercise execution"
    )
    sets: list[SetCreate] = Field(
        default_factory=list, description="Sets for this exercise"
    )


class ExerciseExecutionUpdate(BaseModel):
    """Schema for updating exercise execution metadata only."""

    note_text: str | None = Field(
        None, description="Optional notes about this exercise execution"
    )
    exercise_order: int | None = Field(
        None, ge=1, description="Order of this exercise in the workout (1-based)"
    )


class ExerciseExecutionResponse(BaseModel):
    """Schema for exercise execution responses."""

    exercise_id: int
    exercise_name: str
    exercise_order: int
    note_text: str | None = None
    created_at: datetime
    updated_at: datetime
    sets: list[SetResponse] = []

    model_config = {"from_attributes": True}


class ExerciseReorderRequest(BaseModel):
    """Schema for reordering exercises in a workout."""

    exercise_ids: list[int] = Field(
        ..., min_length=1, description="List of exercise IDs in desired order"
    )


class ExerciseReorderResponse(BaseModel):
    """Schema for exercise reorder responses."""

    message: str
    exercise_executions: list[ExerciseExecutionResponse]


class Pagination(BaseModel):
    """Pagination parameters."""

    page: int = Field(1, ge=1, description="Page number (1-based)")
    size: int = Field(20, ge=1, le=100, description="Page size (max 100)")

    @property
    def offset(self) -> int:
        """Calculate offset for database queries."""
        return (self.page - 1) * self.size


class Page[T](BaseModel):
    """Generic paginated response."""

    items: list[T]
    total: int = Field(..., description="Total number of items")
    page: int = Field(..., description="Current page number")
    size: int = Field(..., description="Page size")
    pages: int = Field(..., description="Total number of pages")

    @classmethod
    def create(cls, items: list[T], total: int, pagination: Pagination) -> "Page[T]":
        """Create a Page instance with calculated values."""
        pages = (total + pagination.size - 1) // pagination.size
        return cls(
            items=items,
            total=total,
            page=pagination.page,
            size=pagination.size,
            pages=pages,
        )
