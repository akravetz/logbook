"""Exercise database models."""

import enum

from sqlalchemy import Boolean, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from ..shared.base_model import BaseModel


class ExerciseModality(str, enum.Enum):
    """Enum for exercise modalities."""

    DUMBBELL = "DUMBBELL"
    BARBELL = "BARBELL"
    CABLE = "CABLE"
    MACHINE = "MACHINE"
    SMITH = "SMITH"
    BODYWEIGHT = "BODYWEIGHT"


class Exercise(BaseModel):
    """Exercise model for storing exercise information."""

    __tablename__ = "exercises"

    name: Mapped[str] = mapped_column(
        String(255), index=True, doc="Name of the exercise"
    )
    body_part: Mapped[str] = mapped_column(
        String(100), index=True, doc="Primary body part targeted by the exercise"
    )
    modality: Mapped[ExerciseModality] = mapped_column(
        Enum(ExerciseModality),
        index=True,
        doc="Equipment/modality used for the exercise",
    )
    picture_url: Mapped[str | None] = mapped_column(
        String(500), doc="URL to exercise demonstration image"
    )
    created_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"),
        doc="ID of user who created this exercise (null for system exercises)",
    )
    updated_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), doc="ID of user who last updated this exercise"
    )
    is_user_created: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        index=True,
        doc="Whether this exercise was created by a user (vs system exercise)",
    )

    def __repr__(self) -> str:
        """String representation of the Exercise."""
        return f"<Exercise(id={self.id}, name='{self.name}', modality={self.modality.value})>"
