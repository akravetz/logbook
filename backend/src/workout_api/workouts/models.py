"""Workout-related database models."""

from datetime import datetime

from sqlalchemy import (
    Float,
    ForeignKey,
    ForeignKeyConstraint,
    Integer,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..shared.base_model import BaseModel


class Workout(BaseModel):
    """Workout model for storing workout sessions."""

    __tablename__ = "workouts"

    finished_at: Mapped[datetime | None] = mapped_column(
        doc="Timestamp when workout was finished (null if in progress)"
    )
    created_by_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), index=True, doc="ID of user who created this workout"
    )
    updated_by_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), doc="ID of user who last updated this workout"
    )

    # Relationships
    exercise_executions: Mapped[list["ExerciseExecution"]] = relationship(
        "ExerciseExecution",
        back_populates="workout",
        cascade="all, delete-orphan",
        order_by="ExerciseExecution.exercise_order",
    )

    def __repr__(self) -> str:
        """String representation of the Workout."""
        status = "finished" if self.finished_at else "in progress"
        return f"<Workout(id={self.id}, user_id={self.created_by_user_id}, status={status})>"


class ExerciseExecution(BaseModel):
    """ExerciseExecution model for exercises performed in a workout."""

    __tablename__ = "exercise_executions"

    workout_id: Mapped[int] = mapped_column(
        ForeignKey("workouts.id"),
        index=True,
        doc="ID of the workout this execution belongs to",
    )
    exercise_id: Mapped[int] = mapped_column(
        ForeignKey("exercises.id"), index=True, doc="ID of the exercise being performed"
    )
    exercise_order: Mapped[int] = mapped_column(
        Integer, doc="Order of this exercise in the workout (1-based)"
    )
    note_text: Mapped[str | None] = mapped_column(
        Text, doc="Optional notes about this exercise execution"
    )

    # Relationships
    workout: Mapped["Workout"] = relationship(
        "Workout", back_populates="exercise_executions"
    )
    sets: Mapped[list["Set"]] = relationship(
        "Set",
        back_populates="exercise_execution",
        cascade="all, delete-orphan",
        order_by="Set.id",
    )

    # Constraints
    __table_args__ = (
        UniqueConstraint("workout_id", "exercise_id", name="uq_workout_exercise"),
    )

    def __repr__(self) -> str:
        """String representation of the ExerciseExecution."""
        return f"<ExerciseExecution(workout_id={self.workout_id}, exercise_id={self.exercise_id}, order={self.exercise_order})>"


class Set(BaseModel):
    """Set model for individual sets within an exercise execution."""

    __tablename__ = "sets"

    workout_id: Mapped[int] = mapped_column(
        ForeignKey("workouts.id"),
        index=True,
        doc="ID of the workout this set belongs to",
    )
    exercise_id: Mapped[int] = mapped_column(
        ForeignKey("exercises.id"),
        index=True,
        doc="ID of the exercise this set belongs to",
    )
    note_text: Mapped[str | None] = mapped_column(
        Text, doc="Optional notes about this set"
    )
    weight: Mapped[float] = mapped_column(
        Float, doc="Weight used for this set (in pounds)"
    )
    clean_reps: Mapped[int] = mapped_column(
        Integer, doc="Number of clean repetitions completed"
    )
    forced_reps: Mapped[int] = mapped_column(
        Integer, default=0, doc="Number of forced repetitions completed"
    )

    # Relationships
    exercise_execution: Mapped["ExerciseExecution"] = relationship(
        "ExerciseExecution",
        back_populates="sets",
        foreign_keys=[workout_id, exercise_id],
    )

    # Foreign key constraint for exercise execution
    __table_args__ = (
        ForeignKeyConstraint(
            ["workout_id", "exercise_id"],
            ["exercise_executions.workout_id", "exercise_executions.exercise_id"],
        ),
    )

    def __repr__(self) -> str:
        """String representation of the Set."""
        return f"<Set(id={self.id}, weight={self.weight}, reps={self.clean_reps}+{self.forced_reps})>"
