"""Workout repository for database operations."""

import logging
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import and_, delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..exercises.models import Exercise
from ..shared.exceptions import NotFoundError, ValidationError
from .models import ExerciseExecution, Set, Workout
from .schemas import (
    ExerciseExecutionRequest,
    ExerciseExecutionUpdate,
    Pagination,
    SetCreate,
    SetUpdate,
    WorkoutFilters,
)

if TYPE_CHECKING:
    from .schemas import Page

logger = logging.getLogger(__name__)


class WorkoutRepository:
    """Repository for workout database operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, workout_id: int, user_id: int) -> Workout | None:
        """Get workout by ID with user permission check."""
        stmt = (
            select(Workout)
            .options(
                selectinload(Workout.exercise_executions).selectinload(
                    ExerciseExecution.sets
                )
            )
            .where(
                and_(
                    Workout.id == workout_id,
                    Workout.created_by_user_id == user_id,
                )
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def search(
        self, filters: WorkoutFilters, pagination: Pagination, user_id: int
    ) -> "Page[Workout]":
        """Search workouts with filters and pagination."""
        # Build base query with user permission
        stmt = (
            select(Workout)
            .options(
                selectinload(Workout.exercise_executions).selectinload(
                    ExerciseExecution.sets
                )
            )
            .where(Workout.created_by_user_id == user_id)
        )

        # Apply filters
        if filters.start_date:
            stmt = stmt.where(Workout.created_at >= filters.start_date)
        if filters.end_date:
            stmt = stmt.where(Workout.created_at <= filters.end_date)
        if filters.finished is not None:
            if filters.finished:
                stmt = stmt.where(Workout.finished_at.is_not(None))
            else:
                stmt = stmt.where(Workout.finished_at.is_(None))

        # Order by created_at descending (most recent first)
        stmt = stmt.order_by(Workout.created_at.desc())

        # Count total results
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_result = await self.session.execute(count_stmt)
        total = total_result.scalar()

        # Apply pagination
        stmt = stmt.offset(pagination.offset).limit(pagination.size)

        result = await self.session.execute(stmt)
        workouts = result.scalars().all()

        # Import here to avoid circular imports
        from .schemas import Page

        return Page.create(list(workouts), total, pagination)

    async def create(self, user_id: int) -> Workout:
        """Create a new workout session."""
        workout = Workout(
            created_by_user_id=user_id,
            updated_by_user_id=user_id,
            finished_at=None,
        )
        self.session.add(workout)
        await self.session.flush()
        await self.session.refresh(workout)
        return workout

    async def finish_workout(self, workout_id: int, user_id: int) -> Workout | None:
        """Finish a workout by setting finished_at timestamp."""
        workout = await self.get_by_id(workout_id, user_id)
        if not workout:
            return None

        if workout.finished_at is not None:
            raise ValidationError("Workout is already finished")

        workout.finished_at = datetime.now(UTC).replace(tzinfo=None)
        workout.updated_by_user_id = user_id
        await self.session.flush()
        await self.session.refresh(workout)
        return workout

    async def delete(self, workout_id: int, user_id: int) -> bool:
        """Delete a workout and all related data."""
        workout = await self.get_by_id(workout_id, user_id)
        if not workout:
            return False

        await self.session.delete(workout)
        return True

    async def get_exercise_execution(
        self, workout_id: int, exercise_id: int, user_id: int
    ) -> tuple[ExerciseExecution, list[Set]] | None:
        """Get exercise execution with sets."""
        # First verify workout exists and user has permission
        workout = await self.get_by_id(workout_id, user_id)
        if not workout:
            return None

        stmt = (
            select(ExerciseExecution)
            .options(selectinload(ExerciseExecution.sets))
            .where(
                and_(
                    ExerciseExecution.workout_id == workout_id,
                    ExerciseExecution.exercise_id == exercise_id,
                )
            )
        )
        result = await self.session.execute(stmt)
        execution = result.scalar_one_or_none()

        if execution:
            return execution, list(execution.sets)
        return None

    async def upsert_exercise_execution(
        self,
        workout_id: int,
        exercise_id: int,
        data: ExerciseExecutionRequest,
        user_id: int,
    ) -> tuple[ExerciseExecution, list[Set]]:
        """Create or update exercise execution with full replacement of sets."""
        # Verify workout exists and user has permission
        workout = await self.get_by_id(workout_id, user_id)
        if not workout:
            raise NotFoundError(f"Workout with ID {workout_id} not found")

        if workout.finished_at is not None:
            raise ValidationError("Cannot modify finished workout")

        # Verify exercise exists
        exercise_stmt = select(Exercise).where(Exercise.id == exercise_id)
        exercise_result = await self.session.execute(exercise_stmt)
        exercise = exercise_result.scalar_one_or_none()
        if not exercise:
            raise NotFoundError(f"Exercise with ID {exercise_id} not found")

        # Check if exercise execution already exists
        existing_execution = await self.session.execute(
            select(ExerciseExecution).where(
                and_(
                    ExerciseExecution.workout_id == workout_id,
                    ExerciseExecution.exercise_id == exercise_id,
                )
            )
        )
        execution = existing_execution.scalar_one_or_none()

        if execution:
            # Update existing execution
            execution.exercise_order = data.exercise_order
            execution.note_text = data.note_text

            # Delete all existing sets
            await self.session.execute(
                delete(Set).where(
                    and_(
                        Set.workout_id == workout_id,
                        Set.exercise_id == exercise_id,
                    )
                )
            )
        else:
            # Create new execution
            execution = ExerciseExecution(
                workout_id=workout_id,
                exercise_id=exercise_id,
                exercise_order=data.exercise_order,
                note_text=data.note_text,
            )
            self.session.add(execution)

        # Create new sets
        sets = []
        for set_data in data.sets:
            new_set = Set(
                workout_id=workout_id,
                exercise_id=exercise_id,
                note_text=set_data.note_text,
                weight=set_data.weight,
                clean_reps=set_data.clean_reps,
                forced_reps=set_data.forced_reps,
            )
            self.session.add(new_set)
            sets.append(new_set)

        await self.session.flush()
        await self.session.refresh(execution)
        for set_obj in sets:
            await self.session.refresh(set_obj)

        return execution, sets

    async def delete_exercise_execution(
        self, workout_id: int, exercise_id: int, user_id: int
    ) -> bool:
        """Delete exercise execution and all its sets."""
        # Verify workout exists and user has permission
        workout = await self.get_by_id(workout_id, user_id)
        if not workout:
            return False

        if workout.finished_at is not None:
            raise ValidationError("Cannot modify finished workout")

        # Get the exercise execution object
        execution_stmt = select(ExerciseExecution).where(
            and_(
                ExerciseExecution.workout_id == workout_id,
                ExerciseExecution.exercise_id == exercise_id,
            )
        )
        result = await self.session.execute(execution_stmt)
        execution = result.scalar_one_or_none()

        if not execution:
            return False

        # Use ORM delete - this triggers cascade="all, delete-orphan"
        await self.session.delete(execution)
        await self.session.flush()  # Ensure deletion is visible within transaction
        self.session.expire_all()  # Clear cached relationships
        return True

    async def create_set(
        self, workout_id: int, exercise_id: int, set_data: SetCreate, user_id: int
    ) -> Set:
        """Create a new set for an exercise execution."""
        # Verify workout exists and user has permission
        workout = await self.get_by_id(workout_id, user_id)
        if not workout:
            raise NotFoundError(f"Workout with ID {workout_id} not found")

        if workout.finished_at is not None:
            raise ValidationError("Cannot modify finished workout")

        # Verify exercise execution exists
        execution_stmt = select(ExerciseExecution).where(
            and_(
                ExerciseExecution.workout_id == workout_id,
                ExerciseExecution.exercise_id == exercise_id,
            )
        )
        execution_result = await self.session.execute(execution_stmt)
        execution = execution_result.scalar_one_or_none()
        if not execution:
            raise NotFoundError(
                f"Exercise execution not found for workout {workout_id} and exercise {exercise_id}"
            )

        new_set = Set(
            workout_id=workout_id,
            exercise_id=exercise_id,
            note_text=set_data.note_text,
            weight=set_data.weight,
            clean_reps=set_data.clean_reps,
            forced_reps=set_data.forced_reps,
        )
        self.session.add(new_set)
        await self.session.flush()
        await self.session.refresh(new_set)
        return new_set

    async def update_set(
        self,
        workout_id: int,
        exercise_id: int,
        set_id: int,
        set_data: SetUpdate,
        user_id: int,
    ) -> Set | None:
        """Update an existing set."""
        # Verify workout exists and user has permission
        workout = await self.get_by_id(workout_id, user_id)
        if not workout:
            return None

        if workout.finished_at is not None:
            raise ValidationError("Cannot modify finished workout")

        # Get the set
        set_stmt = select(Set).where(
            and_(
                Set.id == set_id,
                Set.workout_id == workout_id,
                Set.exercise_id == exercise_id,
            )
        )
        set_result = await self.session.execute(set_stmt)
        set_obj = set_result.scalar_one_or_none()
        if not set_obj:
            return None

        # Update fields that are provided
        update_data = set_data.model_dump(exclude_none=True)
        for field, value in update_data.items():
            setattr(set_obj, field, value)

        await self.session.flush()
        await self.session.refresh(set_obj)
        return set_obj

    async def delete_set(
        self, workout_id: int, exercise_id: int, set_id: int, user_id: int
    ) -> bool:
        """Delete a specific set."""
        # Verify workout exists and user has permission
        workout = await self.get_by_id(workout_id, user_id)
        if not workout:
            return False

        if workout.finished_at is not None:
            raise ValidationError("Cannot modify finished workout")

        # Get the set object
        set_stmt = select(Set).where(
            and_(
                Set.id == set_id,
                Set.workout_id == workout_id,
                Set.exercise_id == exercise_id,
            )
        )
        result = await self.session.execute(set_stmt)
        set_obj = result.scalar_one_or_none()

        if not set_obj:
            return False

        # Use ORM delete
        await self.session.delete(set_obj)
        await self.session.flush()  # Ensure deletion is visible within transaction
        self.session.expire_all()  # Clear cached relationships
        return True

    async def update_exercise_execution_metadata(
        self,
        workout_id: int,
        exercise_id: int,
        data: ExerciseExecutionUpdate,
        user_id: int,
    ) -> ExerciseExecution | None:
        """Update exercise execution metadata (notes, order) without touching sets."""
        # Verify workout exists and user has permission
        workout = await self.get_by_id(workout_id, user_id)
        if not workout:
            return None

        if workout.finished_at is not None:
            raise ValidationError("Cannot modify finished workout")

        # Get the exercise execution
        execution_stmt = select(ExerciseExecution).where(
            and_(
                ExerciseExecution.workout_id == workout_id,
                ExerciseExecution.exercise_id == exercise_id,
            )
        )
        execution_result = await self.session.execute(execution_stmt)
        execution = execution_result.scalar_one_or_none()
        if not execution:
            return None

        # Update fields that are provided
        update_data = data.model_dump(exclude_none=True)
        for field, value in update_data.items():
            setattr(execution, field, value)

        await self.session.flush()
        await self.session.refresh(execution)
        return execution

    async def reorder_exercise_executions(
        self, workout_id: int, exercise_ids: list[int], user_id: int
    ) -> list[ExerciseExecution]:
        """Reorder exercise executions in a workout."""
        # Verify workout exists and user has permission
        workout = await self.get_by_id(workout_id, user_id)
        if not workout:
            raise NotFoundError(f"Workout with ID {workout_id} not found")

        if workout.finished_at is not None:
            raise ValidationError("Cannot modify finished workout")

        # Get all exercise executions for this workout
        executions_stmt = select(ExerciseExecution).where(
            ExerciseExecution.workout_id == workout_id
        )
        executions_result = await self.session.execute(executions_stmt)
        executions = executions_result.scalars().all()

        # Verify all provided exercise_ids exist in the workout
        existing_exercise_ids = {execution.exercise_id for execution in executions}
        provided_exercise_ids = set(exercise_ids)

        if existing_exercise_ids != provided_exercise_ids:
            missing = existing_exercise_ids - provided_exercise_ids
            extra = provided_exercise_ids - existing_exercise_ids
            error_msg = "Exercise ID mismatch in reorder request"
            if missing:
                error_msg += f". Missing: {missing}"
            if extra:
                error_msg += f". Extra: {extra}"
            raise ValidationError(error_msg)

        # Update exercise order
        execution_map = {execution.exercise_id: execution for execution in executions}
        updated_executions = []

        for order, exercise_id in enumerate(exercise_ids, start=1):
            execution = execution_map[exercise_id]
            execution.exercise_order = order
            updated_executions.append(execution)

        await self.session.flush()
        for execution in updated_executions:
            await self.session.refresh(execution)

        return updated_executions
