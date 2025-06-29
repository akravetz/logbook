"""User Pydantic schemas for API requests and responses."""

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, HttpUrl


class UserResponse(BaseModel):
    """User profile response schema."""

    id: int = Field(..., description="User's unique identifier")
    email_address: EmailStr = Field(..., description="User's email address")
    google_id: str = Field(..., description="User's Google OAuth ID")
    name: str = Field(..., description="User's display name")
    profile_image_url: HttpUrl | None = Field(
        None, description="URL to user's profile image"
    )
    is_active: bool = Field(..., description="Whether the user account is active")
    is_admin: bool = Field(..., description="Whether the user has admin privileges")
    created_at: datetime = Field(..., description="When the user account was created")
    updated_at: datetime = Field(
        ..., description="When the user account was last updated"
    )

    model_config = {"from_attributes": True}


class UserProfileUpdate(BaseModel):
    """Schema for updating user profile."""

    name: str | None = Field(
        None, min_length=1, max_length=255, description="Updated display name"
    )
    profile_image_url: HttpUrl | None = Field(
        None, description="Updated profile image URL"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "John Doe",
                "profile_image_url": "https://example.com/profile.jpg",
            }
        }
    }


class ExerciseStats(BaseModel):
    """Statistics for a single exercise."""

    exercise_id: int = Field(..., description="Exercise unique identifier")
    exercise_name: str = Field(..., description="Exercise name")
    count: int = Field(..., description="Number of times performed")
    total_sets: int = Field(..., description="Total number of sets")
    total_volume: float = Field(..., description="Total volume (weight * reps)")


class PersonalRecord(BaseModel):
    """Personal record for an exercise."""

    exercise_id: int = Field(..., description="Exercise unique identifier")
    exercise_name: str = Field(..., description="Exercise name")
    max_weight: float = Field(..., description="Maximum weight lifted")
    achieved_date: datetime = Field(..., description="Date the PR was achieved")
    max_volume_single_set: float = Field(
        ..., description="Maximum volume in a single set"
    )


class StreakInfo(BaseModel):
    """User workout streak information."""

    current_streak: int = Field(..., description="Current consecutive workout days")
    longest_streak: int = Field(..., description="Longest consecutive workout streak")
    last_workout_date: datetime | None = Field(None, description="Date of last workout")


class WorkoutFrequency(BaseModel):
    """Workout frequency statistics."""

    weekly_average: float = Field(..., description="Average workouts per week")
    monthly_counts: dict[str, int] = Field(
        ..., description="Workout counts by month (YYYY-MM)"
    )


class UserStatsResponse(BaseModel):
    """User workout statistics response."""

    total_workouts: int = Field(..., description="Total number of workouts completed")
    total_exercises_performed: int = Field(
        ..., description="Total number of exercises performed"
    )
    total_sets: int = Field(..., description="Total number of sets completed")
    total_weight_lifted: float = Field(
        ..., description="Total weight lifted across all workouts"
    )
    workout_frequency: WorkoutFrequency = Field(
        ..., description="Workout frequency statistics"
    )
    most_performed_exercises: list[ExerciseStats] = Field(
        ..., description="Top exercises by frequency"
    )
    body_part_distribution: dict[str, int] = Field(
        ..., description="Distribution of exercises by body part"
    )
    personal_records: list[PersonalRecord] = Field(
        ..., description="User's personal records"
    )
    streak_info: StreakInfo = Field(..., description="Workout streak information")

    model_config = {
        "json_schema_extra": {
            "example": {
                "total_workouts": 45,
                "total_exercises_performed": 215,
                "total_sets": 687,
                "total_weight_lifted": 45670.5,
                "workout_frequency": {
                    "weekly_average": 3.2,
                    "monthly_counts": {"2024-01": 12, "2024-02": 10, "2024-03": 13},
                },
                "most_performed_exercises": [
                    {
                        "exercise_id": 1,
                        "exercise_name": "Push-ups",
                        "count": 42,
                        "total_sets": 126,
                        "total_volume": 0.0,
                    }
                ],
                "body_part_distribution": {"chest": 82, "legs": 68, "back": 55},
                "personal_records": [
                    {
                        "exercise_id": 15,
                        "exercise_name": "Squats",
                        "max_weight": 225.0,
                        "achieved_date": "2024-03-15T00:00:00Z",
                        "max_volume_single_set": 2700.0,
                    }
                ],
                "streak_info": {
                    "current_streak": 5,
                    "longest_streak": 21,
                    "last_workout_date": "2024-04-28T00:00:00Z",
                },
            }
        }
    }
