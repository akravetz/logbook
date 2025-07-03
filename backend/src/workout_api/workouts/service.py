"""Workout service for business logic and data conversion."""

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..exercises.models import Exercise
from ..shared.exceptions import NotFoundError
from .models import ExerciseExecution, Set, Workout
from .repository import WorkoutRepository
from .schemas import (
    ExerciseExecutionRequest,
    ExerciseExecutionResponse,
    ExerciseExecutionUpdate,
    ExerciseReorderResponse,
    Page,
    Pagination,
    SetCreate,
    SetResponse,
    SetUpdate,
    WorkoutFilters,
    WorkoutResponse,
)

logger = logging.getLogger(__name__)


class WorkoutService:
    """Service for workout business logic and data conversion."""

    def __init__(self, repository: WorkoutRepository, session: AsyncSession):
        self.repository = repository
        self.session = session

    async def get_workouts(
        self, filters: WorkoutFilters, pagination: Pagination, user_id: int
    ) -> "Page[WorkoutResponse]":
        """Get user workouts with filters and pagination."""
        page = await self.repository.search(filters, pagination, user_id)

        # Convert SQLAlchemy objects to Pydantic models within session context
        workout_responses = []
        for workout in page.items:
            workout_response = await self._workout_to_response(workout)
            workout_responses.append(workout_response)

        return Page.create(workout_responses, page.total, pagination)

    async def get_workout(self, workout_id: int, user_id: int) -> WorkoutResponse:
        """Get a single workout with full details."""
        workout = await self.repository.get_by_id(workout_id, user_id)
        if not workout:
            raise NotFoundError(f"Workout with ID {workout_id} not found")

        # Convert to Pydantic model within session context
        return await self._workout_to_response(workout)

    async def create_workout(self, user_id: int) -> WorkoutResponse:
        """Create a new workout session."""
        workout = await self.repository.create(user_id)

        # For newly created workouts, we know there are no exercise executions
        response = WorkoutResponse(
            id=workout.id,
            finished_at=workout.finished_at,
            created_by_user_id=workout.created_by_user_id,
            updated_by_user_id=workout.updated_by_user_id,
            created_at=workout.created_at,
            updated_at=workout.updated_at,
            exercise_executions=[],  # New workouts have no exercise executions
        )
        await self.session.commit()

        return response

    async def finish_workout(self, workout_id: int, user_id: int) -> WorkoutResponse:
        """Finish a workout session."""
        workout = await self.repository.finish_workout(workout_id, user_id)
        if not workout:
            raise NotFoundError(f"Workout with ID {workout_id} not found")

        # Convert to Pydantic model BEFORE commit to avoid lazy loading issues
        response = await self._workout_to_response(workout)
        await self.session.commit()

        return response

    async def delete_workout(self, workout_id: int, user_id: int) -> bool:
        """Delete a workout."""
        success = await self.repository.delete(workout_id, user_id)
        if not success:
            raise NotFoundError(f"Workout with ID {workout_id} not found")

        await self.session.commit()
        return True

    async def get_exercise_execution(
        self, workout_id: int, exercise_id: int, user_id: int
    ) -> ExerciseExecutionResponse:
        """Get exercise execution with sets."""
        result = await self.repository.get_exercise_execution(
            workout_id, exercise_id, user_id
        )
        if not result:
            raise NotFoundError(
                f"Exercise execution not found for workout {workout_id} and exercise {exercise_id}"
            )

        execution, sets = result

        # Convert to Pydantic model within session context
        return await self._exercise_execution_to_response(execution, sets)

    async def upsert_exercise_execution(
        self,
        workout_id: int,
        exercise_id: int,
        data: ExerciseExecutionRequest,
        user_id: int,
    ) -> ExerciseExecutionResponse:
        """Create or update exercise execution with full replacement of sets."""
        execution, sets = await self.repository.upsert_exercise_execution(
            workout_id, exercise_id, data, user_id
        )

        # Convert to Pydantic model BEFORE commit to avoid lazy loading issues
        response = await self._exercise_execution_to_response(execution, sets)
        await self.session.commit()

        return response

    async def delete_exercise_execution(
        self, workout_id: int, exercise_id: int, user_id: int
    ) -> bool:
        """Delete exercise execution and all its sets."""
        success = await self.repository.delete_exercise_execution(
            workout_id, exercise_id, user_id
        )
        if not success:
            raise NotFoundError(
                f"Exercise execution not found for workout {workout_id} and exercise {exercise_id}"
            )

        await self.session.commit()
        return True

    async def create_set(
        self, workout_id: int, exercise_id: int, set_data: SetCreate, user_id: int
    ) -> SetResponse:
        """Create a new set for an exercise execution."""
        set_obj = await self.repository.create_set(
            workout_id, exercise_id, set_data, user_id
        )

        # Convert to Pydantic model BEFORE commit to avoid lazy loading issues
        response = SetResponse.model_validate(set_obj)
        await self.session.commit()

        return response

    async def update_set(
        self,
        workout_id: int,
        exercise_id: int,
        set_id: int,
        set_data: SetUpdate,
        user_id: int,
    ) -> SetResponse:
        """Update an existing set."""
        set_obj = await self.repository.update_set(
            workout_id, exercise_id, set_id, set_data, user_id
        )
        if not set_obj:
            raise NotFoundError(f"Set with ID {set_id} not found")

        # Convert to Pydantic model BEFORE commit to avoid lazy loading issues
        response = SetResponse.model_validate(set_obj)
        await self.session.commit()

        return response

    async def delete_set(
        self, workout_id: int, exercise_id: int, set_id: int, user_id: int
    ) -> bool:
        """Delete a specific set."""
        success = await self.repository.delete_set(
            workout_id, exercise_id, set_id, user_id
        )
        if not success:
            raise NotFoundError(f"Set with ID {set_id} not found")

        await self.session.commit()
        return True

    async def update_exercise_execution(
        self,
        workout_id: int,
        exercise_id: int,
        data: ExerciseExecutionUpdate,
        user_id: int,
    ) -> ExerciseExecutionResponse:
        """Update exercise execution metadata (notes, order) without touching sets."""
        execution = await self.repository.update_exercise_execution_metadata(
            workout_id, exercise_id, data, user_id
        )
        if not execution:
            raise NotFoundError(
                f"Exercise execution not found for workout {workout_id} and exercise {exercise_id}"
            )

        await self.session.commit()

        # Get sets for complete response
        result = await self.repository.get_exercise_execution(
            workout_id, exercise_id, user_id
        )
        if not result:
            raise NotFoundError("Exercise execution not found after update")

        execution, sets = result
        return await self._exercise_execution_to_response(execution, sets)

    async def reorder_exercises(
        self, workout_id: int, exercise_ids: list[int], user_id: int
    ) -> ExerciseReorderResponse:
        """Reorder exercises in a workout."""
        executions = await self.repository.reorder_exercise_executions(
            workout_id, exercise_ids, user_id
        )

        # Convert to Pydantic models BEFORE commit to avoid lazy loading issues
        execution_responses = []
        for execution in executions:
            # Extract exercise_id early to avoid lazy loading issues
            exercise_id = execution.exercise_id

            # Get sets for each execution
            result = await self.repository.get_exercise_execution(
                workout_id, exercise_id, user_id
            )
            if result:
                _, sets = result
                execution_response = await self._exercise_execution_to_response(
                    execution, sets
                )
                execution_responses.append(execution_response)

        await self.session.commit()

        return ExerciseReorderResponse(
            message="Exercise order updated successfully",
            exercise_executions=execution_responses,
        )

    async def _workout_to_response(self, workout: Workout) -> WorkoutResponse:
        """Convert Workout SQLAlchemy object to Pydantic model."""
        # Extract basic attributes early to avoid lazy loading issues
        workout_id = workout.id
        finished_at = workout.finished_at
        created_by_user_id = workout.created_by_user_id
        updated_by_user_id = workout.updated_by_user_id
        created_at = workout.created_at
        updated_at = workout.updated_at

        # Get exercise executions via explicit query to avoid lazy loading issues
        execution_responses = []
        try:
            # Query for exercise executions explicitly instead of using the relationship
            execution_stmt = (
                select(ExerciseExecution)
                .where(ExerciseExecution.workout_id == workout_id)
                .order_by(ExerciseExecution.exercise_order)
            )
            execution_result = await self.session.execute(execution_stmt)
            executions = execution_result.scalars().all()

            for execution in executions:
                # Query for sets explicitly
                set_stmt = (
                    select(Set)
                    .where(
                        Set.workout_id == workout_id,
                        Set.exercise_id == execution.exercise_id,
                    )
                    .order_by(Set.created_at)
                )
                set_result = await self.session.execute(set_stmt)
                sets = set_result.scalars().all()

                execution_response = await self._exercise_execution_to_response(
                    execution, list(sets)
                )
                execution_responses.append(execution_response)
        except Exception:
            # If anything fails, return empty exercise executions
            execution_responses = []

        return WorkoutResponse(
            id=workout_id,
            finished_at=finished_at,
            created_by_user_id=created_by_user_id,
            updated_by_user_id=updated_by_user_id,
            created_at=created_at,
            updated_at=updated_at,
            exercise_executions=execution_responses,
        )

    async def _exercise_execution_to_response(
        self, execution: ExerciseExecution, sets: list[Set]
    ) -> ExerciseExecutionResponse:
        """Convert ExerciseExecution SQLAlchemy object to Pydantic model."""
        # Extract attributes early to avoid lazy loading issues
        exercise_id = execution.exercise_id
        exercise_order = execution.exercise_order
        note_text = execution.note_text
        created_at = execution.created_at
        updated_at = execution.updated_at

        # Get exercise name - need to query exercise table
        exercise_stmt = select(Exercise.name).where(Exercise.id == exercise_id)
        exercise_result = await self.session.execute(exercise_stmt)
        exercise_name = exercise_result.scalar_one()

        # Convert sets to Pydantic models
        set_responses = [SetResponse.model_validate(set_obj) for set_obj in sets]

        return ExerciseExecutionResponse(
            exercise_id=exercise_id,
            exercise_name=exercise_name,
            exercise_order=exercise_order,
            note_text=note_text,
            created_at=created_at,
            updated_at=updated_at,
            sets=set_responses,
        )
