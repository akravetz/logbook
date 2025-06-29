"""Tests for workout repository."""

from datetime import UTC, datetime

import pytest

from workout_api.exercises.models import Exercise
from workout_api.shared.exceptions import NotFoundError, ValidationError
from workout_api.users.models import User
from workout_api.workouts.models import Workout
from workout_api.workouts.repository import WorkoutRepository
from workout_api.workouts.schemas import (
    ExerciseExecutionRequest,
    ExerciseExecutionUpdate,
    Pagination,
    SetCreate,
    SetUpdate,
    WorkoutFilters,
)

pytestmark = pytest.mark.anyio


class TestWorkoutRepository:
    """Test workout repository operations."""

    async def test_create_workout(
        self, workout_repository: WorkoutRepository, test_user: User
    ):
        """Test creating a new workout."""
        user_id = test_user.id

        workout = await workout_repository.create(user_id)

        assert workout.id is not None
        assert workout.created_by_user_id == user_id
        assert workout.updated_by_user_id == user_id
        assert workout.finished_at is None
        assert workout.created_at is not None
        assert workout.updated_at is not None

    async def test_get_by_id_success(
        self,
        workout_repository: WorkoutRepository,
        sample_workout: Workout,
        test_user: User,
    ):
        """Test getting workout by ID successfully."""
        user_id = test_user.id
        workout_id = sample_workout.id

        result = await workout_repository.get_by_id(workout_id, user_id)

        assert result is not None
        assert result.id == workout_id
        assert result.created_by_user_id == user_id

    async def test_get_by_id_wrong_user(
        self,
        workout_repository: WorkoutRepository,
        sample_workout: Workout,
        another_user: User,
    ):
        """Test getting workout by ID with wrong user returns None."""
        workout_id = sample_workout.id
        wrong_user_id = another_user.id

        result = await workout_repository.get_by_id(workout_id, wrong_user_id)

        assert result is None

    async def test_get_by_id_not_found(
        self, workout_repository: WorkoutRepository, test_user: User
    ):
        """Test getting non-existent workout returns None."""
        user_id = test_user.id

        result = await workout_repository.get_by_id(99999, user_id)

        assert result is None

    async def test_search_no_filters(
        self,
        workout_repository: WorkoutRepository,
        sample_workout: Workout,
        test_user: User,
    ):
        """Test searching workouts without filters."""
        user_id = test_user.id
        filters = WorkoutFilters()
        pagination = Pagination(page=1, size=10)

        page = await workout_repository.search(filters, pagination, user_id)

        assert page.total >= 1
        assert len(page.items) >= 1
        assert any(w.id == sample_workout.id for w in page.items)

    async def test_search_with_finished_filter(
        self,
        workout_repository: WorkoutRepository,
        sample_workout: Workout,
        finished_workout: Workout,
        test_user: User,
    ):
        """Test searching workouts with finished filter."""
        user_id = test_user.id

        # Test unfinished workouts
        filters = WorkoutFilters(finished=False)
        pagination = Pagination(page=1, size=10)
        page = await workout_repository.search(filters, pagination, user_id)

        assert any(w.id == sample_workout.id for w in page.items)
        assert not any(w.id == finished_workout.id for w in page.items)

        # Test finished workouts
        filters = WorkoutFilters(finished=True)
        page = await workout_repository.search(filters, pagination, user_id)

        assert not any(w.id == sample_workout.id for w in page.items)
        assert any(w.id == finished_workout.id for w in page.items)

    async def test_search_with_date_filters(
        self,
        workout_repository: WorkoutRepository,
        sample_workout: Workout,
        test_user: User,
    ):
        """Test searching workouts with date filters."""
        user_id = test_user.id

        # Test start_date filter
        start_date = datetime.now(UTC).replace(
            tzinfo=None, hour=0, minute=0, second=0, microsecond=0
        )
        filters = WorkoutFilters(start_date=start_date)
        pagination = Pagination(page=1, size=10)
        page = await workout_repository.search(filters, pagination, user_id)

        assert any(w.id == sample_workout.id for w in page.items)

        # Test end_date filter (future date should include all)
        end_date = datetime.now(UTC).replace(tzinfo=None, hour=23, minute=59, second=59)
        filters = WorkoutFilters(end_date=end_date)
        page = await workout_repository.search(filters, pagination, user_id)

        assert any(w.id == sample_workout.id for w in page.items)

    async def test_search_pagination(
        self, workout_repository: WorkoutRepository, test_user: User
    ):
        """Test workout search pagination."""
        user_id = test_user.id

        # Create multiple workouts
        for _i in range(5):
            await workout_repository.create(user_id)

        filters = WorkoutFilters()
        pagination = Pagination(page=1, size=2)
        page = await workout_repository.search(filters, pagination, user_id)

        assert page.total >= 5
        assert len(page.items) == 2
        assert page.page == 1
        assert page.size == 2
        assert page.pages >= 3

    async def test_finish_workout_success(
        self,
        workout_repository: WorkoutRepository,
        sample_workout: Workout,
        test_user: User,
    ):
        """Test finishing a workout successfully."""
        user_id = test_user.id
        workout_id = sample_workout.id

        result = await workout_repository.finish_workout(workout_id, user_id)

        assert result is not None
        assert result.finished_at is not None
        assert result.updated_by_user_id == user_id

    async def test_finish_workout_already_finished(
        self,
        workout_repository: WorkoutRepository,
        finished_workout: Workout,
        test_user: User,
    ):
        """Test finishing an already finished workout raises error."""
        user_id = test_user.id
        workout_id = finished_workout.id

        with pytest.raises(ValidationError, match="already finished"):
            await workout_repository.finish_workout(workout_id, user_id)

    async def test_finish_workout_not_found(
        self, workout_repository: WorkoutRepository, test_user: User
    ):
        """Test finishing non-existent workout returns None."""
        user_id = test_user.id

        result = await workout_repository.finish_workout(99999, user_id)

        assert result is None

    async def test_delete_workout_success(
        self,
        workout_repository: WorkoutRepository,
        sample_workout: Workout,
        test_user: User,
    ):
        """Test deleting workout successfully."""
        user_id = test_user.id
        workout_id = sample_workout.id

        result = await workout_repository.delete(workout_id, user_id)

        assert result is True
        # Verify workout is deleted
        deleted_workout = await workout_repository.get_by_id(workout_id, user_id)
        assert deleted_workout is None

    async def test_delete_workout_not_found(
        self, workout_repository: WorkoutRepository, test_user: User
    ):
        """Test deleting non-existent workout returns False."""
        user_id = test_user.id

        result = await workout_repository.delete(99999, user_id)

        assert result is False

    async def test_get_exercise_execution_success(
        self,
        workout_repository: WorkoutRepository,
        workout_with_exercises: Workout,
        sample_exercise: Exercise,
        test_user: User,
    ):
        """Test getting exercise execution successfully."""
        user_id = test_user.id
        workout_id = workout_with_exercises.id
        exercise_id = sample_exercise.id

        result = await workout_repository.get_exercise_execution(
            workout_id, exercise_id, user_id
        )

        assert result is not None
        execution, sets = result
        assert execution.workout_id == workout_id
        assert execution.exercise_id == exercise_id
        assert len(sets) == 2  # Two sets for the first exercise

    async def test_get_exercise_execution_not_found(
        self,
        workout_repository: WorkoutRepository,
        sample_workout: Workout,
        sample_exercise: Exercise,
        test_user: User,
    ):
        """Test getting non-existent exercise execution returns None."""
        user_id = test_user.id
        workout_id = sample_workout.id
        exercise_id = sample_exercise.id

        result = await workout_repository.get_exercise_execution(
            workout_id, exercise_id, user_id
        )

        assert result is None

    async def test_upsert_exercise_execution_create(
        self,
        workout_repository: WorkoutRepository,
        sample_workout: Workout,
        sample_exercise: Exercise,
        test_user: User,
    ):
        """Test creating new exercise execution."""
        user_id = test_user.id
        workout_id = sample_workout.id
        exercise_id = sample_exercise.id

        data = ExerciseExecutionRequest(
            exercise_order=1,
            note_text="Test notes",
            sets=[
                SetCreate(weight=20.0, clean_reps=10, forced_reps=0, note_text="Set 1"),
                SetCreate(weight=25.0, clean_reps=8, forced_reps=2, note_text="Set 2"),
            ],
        )

        execution, sets = await workout_repository.upsert_exercise_execution(
            workout_id, exercise_id, data, user_id
        )

        assert execution.workout_id == workout_id
        assert execution.exercise_id == exercise_id
        assert execution.exercise_order == 1
        assert execution.note_text == "Test notes"
        assert len(sets) == 2
        assert sets[0].weight == 20.0
        assert sets[1].weight == 25.0

    async def test_upsert_exercise_execution_update(
        self,
        workout_repository: WorkoutRepository,
        workout_with_exercises: Workout,
        sample_exercise: Exercise,
        test_user: User,
    ):
        """Test updating existing exercise execution (full replace)."""
        user_id = test_user.id
        workout_id = workout_with_exercises.id
        exercise_id = sample_exercise.id

        data = ExerciseExecutionRequest(
            exercise_order=3,
            note_text="Updated notes",
            sets=[
                SetCreate(
                    weight=30.0, clean_reps=6, forced_reps=1, note_text="New set"
                ),
            ],
        )

        execution, sets = await workout_repository.upsert_exercise_execution(
            workout_id, exercise_id, data, user_id
        )

        assert execution.exercise_order == 3
        assert execution.note_text == "Updated notes"
        assert len(sets) == 1  # Should replace all previous sets
        assert sets[0].weight == 30.0

    async def test_upsert_exercise_execution_finished_workout(
        self,
        workout_repository: WorkoutRepository,
        finished_workout: Workout,
        sample_exercise: Exercise,
        test_user: User,
    ):
        """Test upserting exercise execution on finished workout raises error."""
        user_id = test_user.id
        workout_id = finished_workout.id
        exercise_id = sample_exercise.id

        data = ExerciseExecutionRequest(
            exercise_order=1,
            note_text="Test",
            sets=[],
        )

        with pytest.raises(ValidationError, match="Cannot modify finished workout"):
            await workout_repository.upsert_exercise_execution(
                workout_id, exercise_id, data, user_id
            )

    async def test_upsert_exercise_execution_invalid_exercise(
        self,
        workout_repository: WorkoutRepository,
        sample_workout: Workout,
        test_user: User,
    ):
        """Test upserting with invalid exercise ID raises error."""
        user_id = test_user.id
        workout_id = sample_workout.id
        invalid_exercise_id = 99999

        data = ExerciseExecutionRequest(
            exercise_order=1,
            note_text="Test",
            sets=[],
        )

        with pytest.raises(NotFoundError, match="Exercise with ID"):
            await workout_repository.upsert_exercise_execution(
                workout_id, invalid_exercise_id, data, user_id
            )

    async def test_delete_exercise_execution_success(
        self,
        workout_repository: WorkoutRepository,
        workout_with_exercises: Workout,
        sample_exercise: Exercise,
        test_user: User,
    ):
        """Test deleting exercise execution successfully."""
        user_id = test_user.id
        workout_id = workout_with_exercises.id
        exercise_id = sample_exercise.id

        result = await workout_repository.delete_exercise_execution(
            workout_id, exercise_id, user_id
        )

        assert result is True

        # Verify execution is deleted
        execution_result = await workout_repository.get_exercise_execution(
            workout_id, exercise_id, user_id
        )
        assert execution_result is None

    async def test_delete_exercise_execution_not_found(
        self,
        workout_repository: WorkoutRepository,
        sample_workout: Workout,
        sample_exercise: Exercise,
        test_user: User,
    ):
        """Test deleting non-existent exercise execution returns False."""
        user_id = test_user.id
        workout_id = sample_workout.id
        exercise_id = sample_exercise.id

        result = await workout_repository.delete_exercise_execution(
            workout_id, exercise_id, user_id
        )

        assert result is False

    async def test_create_set_success(
        self,
        workout_repository: WorkoutRepository,
        workout_with_exercises: Workout,
        sample_exercise: Exercise,
        test_user: User,
    ):
        """Test creating a new set successfully."""
        user_id = test_user.id
        workout_id = workout_with_exercises.id
        exercise_id = sample_exercise.id

        set_data = SetCreate(
            weight=35.0,
            clean_reps=5,
            forced_reps=3,
            note_text="New set",
        )

        new_set = await workout_repository.create_set(
            workout_id, exercise_id, set_data, user_id
        )

        assert new_set.workout_id == workout_id
        assert new_set.exercise_id == exercise_id
        assert new_set.weight == 35.0
        assert new_set.clean_reps == 5
        assert new_set.forced_reps == 3
        assert new_set.note_text == "New set"

    async def test_create_set_no_execution(
        self,
        workout_repository: WorkoutRepository,
        sample_workout: Workout,
        sample_exercise: Exercise,
        test_user: User,
    ):
        """Test creating set without exercise execution raises error."""
        user_id = test_user.id
        workout_id = sample_workout.id
        exercise_id = sample_exercise.id

        set_data = SetCreate(weight=20.0, clean_reps=10, forced_reps=0)

        with pytest.raises(NotFoundError, match="Exercise execution not found"):
            await workout_repository.create_set(
                workout_id, exercise_id, set_data, user_id
            )

    async def test_update_set_success(
        self,
        workout_repository: WorkoutRepository,
        workout_with_exercises: Workout,
        sample_exercise: Exercise,
        test_user: User,
    ):
        """Test updating a set successfully."""
        user_id = test_user.id
        workout_id = workout_with_exercises.id
        exercise_id = sample_exercise.id

        # Get first set
        result = await workout_repository.get_exercise_execution(
            workout_id, exercise_id, user_id
        )
        _, sets = result
        set_id = sets[0].id

        update_data = SetUpdate(
            weight=25.0,
            clean_reps=15,
            note_text="Updated set",
        )

        updated_set = await workout_repository.update_set(
            workout_id, exercise_id, set_id, update_data, user_id
        )

        assert updated_set is not None
        assert updated_set.weight == 25.0
        assert updated_set.clean_reps == 15
        assert updated_set.note_text == "Updated set"
        assert updated_set.forced_reps == 0  # Should remain unchanged

    async def test_update_set_not_found(
        self,
        workout_repository: WorkoutRepository,
        workout_with_exercises: Workout,
        sample_exercise: Exercise,
        test_user: User,
    ):
        """Test updating non-existent set returns None."""
        user_id = test_user.id
        workout_id = workout_with_exercises.id
        exercise_id = sample_exercise.id
        invalid_set_id = 99999

        update_data = SetUpdate(weight=25.0)

        result = await workout_repository.update_set(
            workout_id, exercise_id, invalid_set_id, update_data, user_id
        )

        assert result is None

    async def test_delete_set_success(
        self,
        workout_repository: WorkoutRepository,
        workout_with_exercises: Workout,
        sample_exercise: Exercise,
        test_user: User,
    ):
        """Test deleting a set successfully."""
        user_id = test_user.id
        workout_id = workout_with_exercises.id
        exercise_id = sample_exercise.id

        # Get first set
        result = await workout_repository.get_exercise_execution(
            workout_id, exercise_id, user_id
        )
        _, sets = result
        set_id = sets[0].id
        initial_count = len(sets)

        delete_result = await workout_repository.delete_set(
            workout_id, exercise_id, set_id, user_id
        )

        assert delete_result is True

        # Verify set is deleted
        result = await workout_repository.get_exercise_execution(
            workout_id, exercise_id, user_id
        )
        _, remaining_sets = result
        assert len(remaining_sets) == initial_count - 1

    async def test_delete_set_not_found(
        self,
        workout_repository: WorkoutRepository,
        workout_with_exercises: Workout,
        sample_exercise: Exercise,
        test_user: User,
    ):
        """Test deleting non-existent set returns False."""
        user_id = test_user.id
        workout_id = workout_with_exercises.id
        exercise_id = sample_exercise.id
        invalid_set_id = 99999

        result = await workout_repository.delete_set(
            workout_id, exercise_id, invalid_set_id, user_id
        )

        assert result is False

    async def test_update_exercise_execution_metadata_success(
        self,
        workout_repository: WorkoutRepository,
        workout_with_exercises: Workout,
        sample_exercise: Exercise,
        test_user: User,
    ):
        """Test updating exercise execution metadata successfully."""
        user_id = test_user.id
        workout_id = workout_with_exercises.id
        exercise_id = sample_exercise.id

        update_data = ExerciseExecutionUpdate(
            note_text="Updated metadata",
            exercise_order=5,
        )

        updated_execution = await workout_repository.update_exercise_execution_metadata(
            workout_id, exercise_id, update_data, user_id
        )

        assert updated_execution is not None
        assert updated_execution.note_text == "Updated metadata"
        assert updated_execution.exercise_order == 5

    async def test_update_exercise_execution_metadata_not_found(
        self,
        workout_repository: WorkoutRepository,
        sample_workout: Workout,
        sample_exercise: Exercise,
        test_user: User,
    ):
        """Test updating non-existent exercise execution metadata returns None."""
        user_id = test_user.id
        workout_id = sample_workout.id
        exercise_id = sample_exercise.id

        update_data = ExerciseExecutionUpdate(note_text="Test")

        result = await workout_repository.update_exercise_execution_metadata(
            workout_id, exercise_id, update_data, user_id
        )

        assert result is None

    async def test_reorder_exercise_executions_success(
        self,
        workout_repository: WorkoutRepository,
        workout_with_exercises: Workout,
        sample_exercise: Exercise,
        another_exercise: Exercise,
        test_user: User,
    ):
        """Test reordering exercise executions successfully."""
        user_id = test_user.id
        workout_id = workout_with_exercises.id
        exercise1_id = sample_exercise.id
        exercise2_id = another_exercise.id

        # Reorder: exercise2 first, then exercise1
        exercise_ids = [exercise2_id, exercise1_id]

        updated_executions = await workout_repository.reorder_exercise_executions(
            workout_id, exercise_ids, user_id
        )

        assert len(updated_executions) == 2

        # Find executions by exercise_id
        ex1_execution = next(
            e for e in updated_executions if e.exercise_id == exercise1_id
        )
        ex2_execution = next(
            e for e in updated_executions if e.exercise_id == exercise2_id
        )

        assert ex2_execution.exercise_order == 1  # Should be first now
        assert ex1_execution.exercise_order == 2  # Should be second now

    async def test_reorder_exercise_executions_mismatch(
        self,
        workout_repository: WorkoutRepository,
        workout_with_exercises: Workout,
        sample_exercise: Exercise,
        test_user: User,
    ):
        """Test reordering with mismatched exercise IDs raises error."""
        user_id = test_user.id
        workout_id = workout_with_exercises.id
        exercise1_id = sample_exercise.id
        invalid_exercise_id = 99999

        # Provide mismatched exercise IDs
        exercise_ids = [exercise1_id, invalid_exercise_id]

        with pytest.raises(ValidationError, match="Exercise ID mismatch"):
            await workout_repository.reorder_exercise_executions(
                workout_id, exercise_ids, user_id
            )
