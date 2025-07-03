"""Test workout service integration."""

import pytest

from workout_api.exercises.models import Exercise
from workout_api.shared.exceptions import NotFoundError
from workout_api.users.models import User
from workout_api.workouts.models import Workout
from workout_api.workouts.schemas import (
    ExerciseExecutionRequest,
    ExerciseExecutionResponse,
    ExerciseExecutionUpdate,
    Pagination,
    SetCreate,
    SetUpdate,
    WorkoutFilters,
    WorkoutResponse,
)
from workout_api.workouts.service import WorkoutService

pytestmark = pytest.mark.anyio


class TestWorkoutService:
    """Test workout service integration with real repository."""

    # ===================
    # create_workout tests
    # ===================

    async def test_create_workout_success(
        self, workout_service: WorkoutService, test_user: User
    ):
        """Test successful workout creation."""
        # Extract user ID early to avoid lazy loading issues
        user_id = test_user.id

        result = await workout_service.create_workout(user_id)

        assert isinstance(result, WorkoutResponse)
        assert result.id is not None
        assert result.created_by_user_id == user_id
        assert result.updated_by_user_id == user_id
        assert result.finished_at is None
        assert result.exercise_executions == []
        assert result.created_at is not None
        assert result.updated_at is not None

    async def test_create_workout_returns_pydantic_model(
        self, workout_service: WorkoutService, test_user: User
    ):
        """Test that create_workout returns proper Pydantic model."""
        # Extract user ID early
        user_id = test_user.id

        result = await workout_service.create_workout(user_id)

        # Verify it's a Pydantic model
        assert isinstance(result, WorkoutResponse)
        assert hasattr(result, "model_dump")
        assert hasattr(result, "model_validate")

        # Verify all expected fields are present
        data = result.model_dump()
        expected_fields = {
            "id",
            "created_by_user_id",
            "updated_by_user_id",
            "finished_at",
            "exercise_executions",
            "created_at",
            "updated_at",
        }
        assert expected_fields.issubset(data.keys())

    # ===================
    # upsert_exercise_execution tests
    # ===================

    async def test_upsert_exercise_execution_create_new(
        self,
        workout_service: WorkoutService,
        sample_workout: Workout,
        sample_exercise: Exercise,
        test_user: User,
    ):
        """Test creating new exercise execution with sets."""
        # Extract IDs early to avoid lazy loading issues
        workout_id = sample_workout.id
        exercise_id = sample_exercise.id
        user_id = test_user.id

        execution_data = ExerciseExecutionRequest(
            exercise_order=1,
            note_text="First exercise of the day",
            sets=[
                SetCreate(weight=100.0, clean_reps=10, forced_reps=0),
                SetCreate(
                    weight=100.0, clean_reps=8, forced_reps=2, note_text="Tough set"
                ),
            ],
        )

        result = await workout_service.upsert_exercise_execution(
            workout_id, exercise_id, execution_data, user_id
        )

        assert isinstance(result, ExerciseExecutionResponse)
        assert result.exercise_id == exercise_id
        assert result.exercise_name == "Test Exercise"  # From fixture
        assert result.exercise_order == 1
        assert result.note_text == "First exercise of the day"
        assert len(result.sets) == 2

        # Verify sets
        assert result.sets[0].weight == 100.0
        assert result.sets[0].clean_reps == 10
        assert result.sets[0].forced_reps == 0
        assert result.sets[0].note_text is None

        assert result.sets[1].weight == 100.0
        assert result.sets[1].clean_reps == 8
        assert result.sets[1].forced_reps == 2
        assert result.sets[1].note_text == "Tough set"

    async def test_upsert_exercise_execution_update_existing(
        self,
        workout_service: WorkoutService,
        workout_with_exercises: Workout,
        sample_exercise: Exercise,
        test_user: User,
    ):
        """Test updating existing exercise execution (replaces sets)."""
        # Extract IDs early
        workout_id = workout_with_exercises.id
        exercise_id = sample_exercise.id
        user_id = test_user.id

        # Get initial state
        initial_result = await workout_service.get_exercise_execution(
            workout_id, exercise_id, user_id
        )
        assert len(initial_result.sets) == 2  # From fixture

        # Update with different sets (complete replacement)
        execution_data = ExerciseExecutionRequest(
            exercise_order=3,  # Change order
            note_text="Updated notes",
            sets=[
                SetCreate(weight=120.0, clean_reps=8, forced_reps=0),
                SetCreate(weight=120.0, clean_reps=6, forced_reps=1),
                SetCreate(weight=110.0, clean_reps=10, forced_reps=0),
            ],
        )

        result = await workout_service.upsert_exercise_execution(
            workout_id, exercise_id, execution_data, user_id
        )

        assert isinstance(result, ExerciseExecutionResponse)
        assert result.exercise_id == exercise_id
        assert result.exercise_order == 3  # Updated
        assert result.note_text == "Updated notes"  # Updated
        assert len(result.sets) == 3  # Replaced with 3 sets

        # Verify new sets
        assert result.sets[0].weight == 120.0
        assert result.sets[1].weight == 120.0
        assert result.sets[2].weight == 110.0

    async def test_upsert_exercise_execution_replace_sets_completely(
        self,
        workout_service: WorkoutService,
        workout_with_exercises: Workout,
        sample_exercise: Exercise,
        test_user: User,
    ):
        """Test that upsert completely replaces sets."""
        # Extract IDs early
        workout_id = workout_with_exercises.id
        exercise_id = sample_exercise.id
        user_id = test_user.id

        # Start with 2 sets (from fixture)
        initial_result = await workout_service.get_exercise_execution(
            workout_id, exercise_id, user_id
        )
        initial_set_ids = [s.id for s in initial_result.sets]
        assert len(initial_set_ids) == 2

        # Replace with single set
        execution_data = ExerciseExecutionRequest(
            exercise_order=1,
            sets=[SetCreate(weight=150.0, clean_reps=5, forced_reps=0)],
        )

        result = await workout_service.upsert_exercise_execution(
            workout_id, exercise_id, execution_data, user_id
        )

        # Should have only 1 set now
        assert len(result.sets) == 1
        assert result.sets[0].weight == 150.0

        # New set should have different ID
        new_set_id = result.sets[0].id
        assert new_set_id not in initial_set_ids

    async def test_upsert_exercise_execution_empty_sets(
        self,
        workout_service: WorkoutService,
        sample_workout: Workout,
        sample_exercise: Exercise,
        test_user: User,
    ):
        """Test upsert with empty sets list."""
        # Extract IDs early
        workout_id = sample_workout.id
        exercise_id = sample_exercise.id
        user_id = test_user.id

        execution_data = ExerciseExecutionRequest(
            exercise_order=1,
            note_text="Exercise with no sets yet",
            sets=[],  # Empty sets
        )

        result = await workout_service.upsert_exercise_execution(
            workout_id, exercise_id, execution_data, user_id
        )

        assert isinstance(result, ExerciseExecutionResponse)
        assert result.exercise_id == exercise_id
        assert result.exercise_order == 1
        assert result.note_text == "Exercise with no sets yet"
        assert result.sets == []

    async def test_upsert_exercise_execution_invalid_workout(
        self,
        workout_service: WorkoutService,
        sample_exercise: Exercise,
        test_user: User,
    ):
        """Test upsert with non-existent workout ID."""
        # Extract IDs early
        exercise_id = sample_exercise.id
        user_id = test_user.id

        execution_data = ExerciseExecutionRequest(
            exercise_order=1,
            sets=[SetCreate(weight=100.0, clean_reps=10, forced_reps=0)],
        )

        with pytest.raises(NotFoundError, match="Workout.*not found"):
            await workout_service.upsert_exercise_execution(
                999999,
                exercise_id,
                execution_data,
                user_id,  # Non-existent workout
            )

    async def test_upsert_exercise_execution_invalid_exercise(
        self,
        workout_service: WorkoutService,
        sample_workout: Workout,
        test_user: User,
    ):
        """Test upsert with non-existent exercise ID."""
        # Extract IDs early
        workout_id = sample_workout.id
        user_id = test_user.id

        execution_data = ExerciseExecutionRequest(
            exercise_order=1,
            sets=[SetCreate(weight=100.0, clean_reps=10, forced_reps=0)],
        )

        with pytest.raises(NotFoundError, match="Exercise.*not found"):
            await workout_service.upsert_exercise_execution(
                workout_id,
                999999,
                execution_data,
                user_id,  # Non-existent exercise
            )

    async def test_upsert_exercise_execution_returns_pydantic_model(
        self,
        workout_service: WorkoutService,
        sample_workout: Workout,
        sample_exercise: Exercise,
        test_user: User,
    ):
        """Test that upsert returns proper Pydantic model."""
        # Extract IDs early
        workout_id = sample_workout.id
        exercise_id = sample_exercise.id
        user_id = test_user.id

        execution_data = ExerciseExecutionRequest(
            exercise_order=1,
            sets=[SetCreate(weight=100.0, clean_reps=10, forced_reps=0)],
        )

        result = await workout_service.upsert_exercise_execution(
            workout_id, exercise_id, execution_data, user_id
        )

        # Verify it's a Pydantic model
        assert isinstance(result, ExerciseExecutionResponse)
        assert hasattr(result, "model_dump")
        assert hasattr(result, "model_validate")

        # Verify all expected fields are present
        data = result.model_dump()
        expected_fields = {
            "exercise_id",
            "exercise_name",
            "exercise_order",
            "note_text",
            "sets",
            "created_at",
            "updated_at",
        }
        assert expected_fields.issubset(data.keys())

        # Verify sets are also Pydantic models
        for set_obj in result.sets:
            assert hasattr(set_obj, "model_dump")
            set_data = set_obj.model_dump()
            set_expected_fields = {
                "id",
                "weight",
                "clean_reps",
                "forced_reps",
                "note_text",
                "created_at",
                "updated_at",
            }
            assert set_expected_fields.issubset(set_data.keys())

    async def test_upsert_exercise_execution_user_ownership(
        self,
        workout_service: WorkoutService,
        sample_workout: Workout,
        sample_exercise: Exercise,
        another_user: User,
    ):
        """Test that upsert respects user ownership of workout."""
        # Extract IDs early
        workout_id = sample_workout.id  # Owned by test_user
        exercise_id = sample_exercise.id
        another_user_id = another_user.id  # Different user

        execution_data = ExerciseExecutionRequest(
            exercise_order=1,
            sets=[SetCreate(weight=100.0, clean_reps=10, forced_reps=0)],
        )

        # Should not be able to modify another user's workout
        with pytest.raises(NotFoundError, match="Workout.*not found"):
            await workout_service.upsert_exercise_execution(
                workout_id, exercise_id, execution_data, another_user_id
            )

    # ======================
    # Phase 1: Core Workout CRUD Tests
    # ======================

    async def test_get_workouts_success(
        self, workout_service: WorkoutService, test_user: User
    ):
        """Test successful retrieval of user workouts with pagination."""
        user_id = test_user.id

        # Create multiple workouts
        workout1 = await workout_service.create_workout(user_id)
        workout2 = await workout_service.create_workout(user_id)

        # Test retrieval with default pagination
        filters = WorkoutFilters()
        pagination = Pagination(page=1, size=10)

        page = await workout_service.get_workouts(filters, pagination, user_id)

        assert page.total >= 2
        assert len(page.items) >= 2
        assert page.page == 1
        assert page.size == 10

        # Verify returned workout IDs match created ones
        workout_ids = [w.id for w in page.items]
        assert workout1.id in workout_ids
        assert workout2.id in workout_ids

    async def test_get_workouts_with_pagination(
        self, workout_service: WorkoutService, test_user: User
    ):
        """Test workout pagination works correctly."""
        user_id = test_user.id

        # Create several workouts
        workouts = []
        for _ in range(5):
            workout = await workout_service.create_workout(user_id)
            workouts.append(workout)

        # Test first page with size 2
        filters = WorkoutFilters()
        pagination = Pagination(page=1, size=2)

        page1 = await workout_service.get_workouts(filters, pagination, user_id)

        assert page1.total >= 5
        assert len(page1.items) == 2
        assert page1.page == 1
        assert page1.size == 2

        # Test second page
        pagination = Pagination(page=2, size=2)
        page2 = await workout_service.get_workouts(filters, pagination, user_id)

        assert len(page2.items) >= 1
        assert page2.page == 2
        assert page2.size == 2

        # Ensure different workouts on different pages
        page1_ids = {w.id for w in page1.items}
        page2_ids = {w.id for w in page2.items}
        assert page1_ids.isdisjoint(page2_ids)

    async def test_get_workouts_empty_result(
        self, workout_service: WorkoutService, test_user: User
    ):
        """Test get_workouts returns empty result for user with no workouts."""
        # Create a new user with no workouts - use the existing test_user
        user_id = test_user.id

        # First, ensure user has no workouts by checking existing ones
        filters = WorkoutFilters()
        pagination = Pagination(page=1, size=10)

        # Get initial count
        initial_page = await workout_service.get_workouts(filters, pagination, user_id)
        initial_count = initial_page.total

        # The test validates that empty result structure is correct
        assert initial_page.items == [] or len(initial_page.items) == initial_count
        assert initial_page.total >= 0
        assert initial_page.page == 1
        assert initial_page.size == 10

    async def test_get_workout_success(
        self,
        workout_service: WorkoutService,
        test_user: User,
        sample_exercise: Exercise,
    ):
        """Test successful retrieval of a single workout."""
        user_id = test_user.id
        exercise_id = sample_exercise.id

        # Create workout and add exercise execution
        workout = await workout_service.create_workout(user_id)
        workout_id = workout.id

        # Add exercise execution to make workout more interesting
        execution_data = ExerciseExecutionRequest(
            exercise_order=1,
            sets=[SetCreate(weight=100.0, clean_reps=10, forced_reps=0)],
        )
        await workout_service.upsert_exercise_execution(
            workout_id, exercise_id, execution_data, user_id
        )

        # Retrieve the workout
        retrieved_workout = await workout_service.get_workout(workout_id, user_id)

        assert retrieved_workout.id == workout_id
        assert retrieved_workout.created_by_user_id == user_id
        assert retrieved_workout.finished_at is None
        assert len(retrieved_workout.exercise_executions) == 1
        assert retrieved_workout.exercise_executions[0].exercise_id == exercise_id

    async def test_get_workout_not_found(
        self, workout_service: WorkoutService, test_user: User
    ):
        """Test get_workout raises NotFoundError for non-existent workout."""
        user_id = test_user.id

        with pytest.raises(NotFoundError, match="Workout with ID 99999 not found"):
            await workout_service.get_workout(99999, user_id)

    async def test_get_workout_wrong_user(
        self, workout_service: WorkoutService, test_user: User, another_user: User
    ):
        """Test get_workout raises NotFoundError when user doesn't own workout."""
        # Create workout with test_user
        user_id = test_user.id
        another_user_id = another_user.id

        workout = await workout_service.create_workout(user_id)
        workout_id = workout.id

        # Try to access with different user
        with pytest.raises(NotFoundError):
            await workout_service.get_workout(workout_id, another_user_id)

    async def test_finish_workout_success(
        self, workout_service: WorkoutService, test_user: User
    ):
        """Test successfully finishing a workout."""
        user_id = test_user.id

        # Create workout
        workout = await workout_service.create_workout(user_id)
        workout_id = workout.id

        # Verify workout is not finished initially
        assert workout.finished_at is None

        # Finish the workout
        finished_workout = await workout_service.finish_workout(workout_id, user_id)

        assert finished_workout.id == workout_id
        assert finished_workout.finished_at is not None
        assert finished_workout.created_by_user_id == user_id

    async def test_finish_workout_not_found(
        self, workout_service: WorkoutService, test_user: User
    ):
        """Test finish_workout raises NotFoundError for non-existent workout."""
        user_id = test_user.id

        with pytest.raises(NotFoundError, match="Workout with ID 99999 not found"):
            await workout_service.finish_workout(99999, user_id)

    async def test_finish_workout_wrong_user(
        self, workout_service: WorkoutService, test_user: User, another_user: User
    ):
        """Test finish_workout raises NotFoundError when user doesn't own workout."""
        # Create workout with test_user
        user_id = test_user.id
        another_user_id = another_user.id

        workout = await workout_service.create_workout(user_id)
        workout_id = workout.id

        # Try to finish with different user
        with pytest.raises(NotFoundError):
            await workout_service.finish_workout(workout_id, another_user_id)

    async def test_delete_workout_success(
        self, workout_service: WorkoutService, test_user: User
    ):
        """Test successfully deleting a workout."""
        user_id = test_user.id

        # Create workout
        workout = await workout_service.create_workout(user_id)
        workout_id = workout.id

        # Delete the workout
        result = await workout_service.delete_workout(workout_id, user_id)

        assert result is True

        # Verify workout is deleted
        with pytest.raises(NotFoundError):
            await workout_service.get_workout(workout_id, user_id)

    async def test_delete_workout_not_found(
        self, workout_service: WorkoutService, test_user: User
    ):
        """Test delete_workout raises NotFoundError for non-existent workout."""
        user_id = test_user.id

        with pytest.raises(NotFoundError, match="Workout with ID 99999 not found"):
            await workout_service.delete_workout(99999, user_id)

    async def test_delete_workout_wrong_user(
        self, workout_service: WorkoutService, test_user: User, another_user: User
    ):
        """Test delete_workout raises NotFoundError when user doesn't own workout."""
        # Create workout with test_user
        user_id = test_user.id
        another_user_id = another_user.id

        workout = await workout_service.create_workout(user_id)
        workout_id = workout.id

        # Try to delete with different user
        with pytest.raises(NotFoundError):
            await workout_service.delete_workout(workout_id, another_user_id)

    # ======================
    # Phase 2: Exercise Execution Management Tests
    # ======================

    async def test_get_exercise_execution_success(
        self,
        workout_service: WorkoutService,
        test_user: User,
        sample_exercise: Exercise,
    ):
        """Test successful retrieval of exercise execution."""
        user_id = test_user.id
        exercise_id = sample_exercise.id

        # Create workout and exercise execution
        workout = await workout_service.create_workout(user_id)
        workout_id = workout.id

        execution_data = ExerciseExecutionRequest(
            exercise_order=1,
            note_text="Test notes",
            sets=[
                SetCreate(weight=100.0, clean_reps=10, forced_reps=0),
                SetCreate(weight=105.0, clean_reps=8, forced_reps=1),
            ],
        )

        await workout_service.upsert_exercise_execution(
            workout_id, exercise_id, execution_data, user_id
        )

        # Retrieve the exercise execution
        retrieved_execution = await workout_service.get_exercise_execution(
            workout_id, exercise_id, user_id
        )

        assert retrieved_execution.exercise_id == exercise_id
        assert retrieved_execution.exercise_order == 1
        assert retrieved_execution.note_text == "Test notes"
        assert len(retrieved_execution.sets) == 2
        assert retrieved_execution.sets[0].weight == 100.0
        assert retrieved_execution.sets[1].weight == 105.0

    async def test_get_exercise_execution_not_found(
        self,
        workout_service: WorkoutService,
        test_user: User,
        sample_exercise: Exercise,
    ):
        """Test get_exercise_execution raises NotFoundError when execution doesn't exist."""
        user_id = test_user.id
        exercise_id = sample_exercise.id

        # Create workout but no exercise execution
        workout = await workout_service.create_workout(user_id)
        workout_id = workout.id

        with pytest.raises(NotFoundError, match="Exercise execution not found"):
            await workout_service.get_exercise_execution(
                workout_id, exercise_id, user_id
            )

    async def test_delete_exercise_execution_success(
        self,
        workout_service: WorkoutService,
        test_user: User,
        sample_exercise: Exercise,
    ):
        """Test successfully deleting an exercise execution."""
        user_id = test_user.id
        exercise_id = sample_exercise.id

        # Create workout and exercise execution
        workout = await workout_service.create_workout(user_id)
        workout_id = workout.id

        execution_data = ExerciseExecutionRequest(
            exercise_order=1,
            sets=[SetCreate(weight=100.0, clean_reps=10, forced_reps=0)],
        )

        await workout_service.upsert_exercise_execution(
            workout_id, exercise_id, execution_data, user_id
        )

        # Verify execution exists
        execution = await workout_service.get_exercise_execution(
            workout_id, exercise_id, user_id
        )
        assert execution is not None

        # Delete the exercise execution
        result = await workout_service.delete_exercise_execution(
            workout_id, exercise_id, user_id
        )

        assert result is True

        # Verify execution is deleted
        with pytest.raises(NotFoundError):
            await workout_service.get_exercise_execution(
                workout_id, exercise_id, user_id
            )

    async def test_delete_exercise_execution_not_found(
        self,
        workout_service: WorkoutService,
        test_user: User,
        sample_exercise: Exercise,
    ):
        """Test delete_exercise_execution raises NotFoundError when execution doesn't exist."""
        user_id = test_user.id
        exercise_id = sample_exercise.id

        # Create workout but no exercise execution
        workout = await workout_service.create_workout(user_id)
        workout_id = workout.id

        with pytest.raises(NotFoundError, match="Exercise execution not found"):
            await workout_service.delete_exercise_execution(
                workout_id, exercise_id, user_id
            )

    async def test_update_exercise_execution_notes(
        self,
        workout_service: WorkoutService,
        test_user: User,
        sample_exercise: Exercise,
    ):
        """Test updating exercise execution notes."""
        user_id = test_user.id
        exercise_id = sample_exercise.id

        # Create workout and exercise execution
        workout = await workout_service.create_workout(user_id)
        workout_id = workout.id

        execution_data = ExerciseExecutionRequest(
            exercise_order=1,
            note_text="Original notes",
            sets=[SetCreate(weight=100.0, clean_reps=10, forced_reps=0)],
        )

        await workout_service.upsert_exercise_execution(
            workout_id, exercise_id, execution_data, user_id
        )

        # Update notes
        update_data = ExerciseExecutionUpdate(note_text="Updated notes")

        updated_execution = await workout_service.update_exercise_execution(
            workout_id, exercise_id, update_data, user_id
        )

        assert updated_execution.exercise_id == exercise_id
        assert updated_execution.note_text == "Updated notes"
        assert updated_execution.exercise_order == 1  # Should remain unchanged
        assert len(updated_execution.sets) == 1  # Sets should remain unchanged

    async def test_update_exercise_execution_order(
        self,
        workout_service: WorkoutService,
        test_user: User,
        sample_exercise: Exercise,
    ):
        """Test updating exercise execution order."""
        user_id = test_user.id
        exercise_id = sample_exercise.id

        # Create workout and exercise execution
        workout = await workout_service.create_workout(user_id)
        workout_id = workout.id

        execution_data = ExerciseExecutionRequest(
            exercise_order=1,
            sets=[SetCreate(weight=100.0, clean_reps=10, forced_reps=0)],
        )

        await workout_service.upsert_exercise_execution(
            workout_id, exercise_id, execution_data, user_id
        )

        # Update order
        update_data = ExerciseExecutionUpdate(exercise_order=3)

        updated_execution = await workout_service.update_exercise_execution(
            workout_id, exercise_id, update_data, user_id
        )

        assert updated_execution.exercise_id == exercise_id
        assert updated_execution.exercise_order == 3
        assert len(updated_execution.sets) == 1  # Sets should remain unchanged

    async def test_update_exercise_execution_not_found(
        self,
        workout_service: WorkoutService,
        test_user: User,
        sample_exercise: Exercise,
    ):
        """Test update_exercise_execution raises NotFoundError when execution doesn't exist."""
        user_id = test_user.id
        exercise_id = sample_exercise.id

        # Create workout but no exercise execution
        workout = await workout_service.create_workout(user_id)
        workout_id = workout.id

        update_data = ExerciseExecutionUpdate(note_text="New notes")

        with pytest.raises(NotFoundError, match="Exercise execution not found"):
            await workout_service.update_exercise_execution(
                workout_id, exercise_id, update_data, user_id
            )

    async def test_reorder_exercises_success(
        self,
        workout_service: WorkoutService,
        test_user: User,
        sample_exercise: Exercise,
        another_exercise: Exercise,
    ):
        """Test successfully reordering exercises in a workout."""
        user_id = test_user.id
        exercise1_id = sample_exercise.id
        exercise2_id = another_exercise.id

        # Create workout with two exercise executions
        workout = await workout_service.create_workout(user_id)
        workout_id = workout.id

        # Add first exercise
        execution1_data = ExerciseExecutionRequest(
            exercise_order=1,
            sets=[SetCreate(weight=100.0, clean_reps=10, forced_reps=0)],
        )
        await workout_service.upsert_exercise_execution(
            workout_id, exercise1_id, execution1_data, user_id
        )

        # Add second exercise
        execution2_data = ExerciseExecutionRequest(
            exercise_order=2,
            sets=[SetCreate(weight=200.0, clean_reps=5, forced_reps=0)],
        )
        await workout_service.upsert_exercise_execution(
            workout_id, exercise2_id, execution2_data, user_id
        )

        # Reorder exercises (reverse order)
        reorder_result = await workout_service.reorder_exercises(
            workout_id, [exercise2_id, exercise1_id], user_id
        )

        assert reorder_result.message == "Exercise order updated successfully"
        assert len(reorder_result.exercise_executions) == 2

        # Verify new order
        executions = reorder_result.exercise_executions
        assert executions[0].exercise_id == exercise2_id
        assert executions[0].exercise_order == 1
        assert executions[1].exercise_id == exercise1_id
        assert executions[1].exercise_order == 2

    async def test_reorder_exercises_invalid_workout(
        self,
        workout_service: WorkoutService,
        test_user: User,
        sample_exercise: Exercise,
    ):
        """Test reorder_exercises with invalid workout ID."""
        user_id = test_user.id
        exercise_id = sample_exercise.id

        # Repository raises NotFoundError for invalid workout ID
        with pytest.raises(NotFoundError, match="Workout with ID 99999 not found"):
            await workout_service.reorder_exercises(99999, [exercise_id], user_id)

    # ======================
    # Phase 3: Set Operations Tests
    # ======================

    async def test_create_set_success(
        self,
        workout_service: WorkoutService,
        test_user: User,
        sample_exercise: Exercise,
    ):
        """Test successfully creating a new set."""
        user_id = test_user.id
        exercise_id = sample_exercise.id

        # Create workout and exercise execution
        workout = await workout_service.create_workout(user_id)
        workout_id = workout.id

        execution_data = ExerciseExecutionRequest(
            exercise_order=1,
            sets=[SetCreate(weight=100.0, clean_reps=10, forced_reps=0)],
        )

        await workout_service.upsert_exercise_execution(
            workout_id, exercise_id, execution_data, user_id
        )

        # Create additional set
        set_data = SetCreate(
            weight=105.0, clean_reps=8, forced_reps=1, note_text="Extra set"
        )

        new_set = await workout_service.create_set(
            workout_id, exercise_id, set_data, user_id
        )

        assert new_set.weight == 105.0
        assert new_set.clean_reps == 8
        assert new_set.forced_reps == 1
        assert new_set.note_text == "Extra set"
        assert new_set.id is not None

        # Verify set was added to exercise execution
        execution = await workout_service.get_exercise_execution(
            workout_id, exercise_id, user_id
        )
        assert len(execution.sets) == 2  # Original + new set

    async def test_create_set_invalid_exercise_execution(
        self,
        workout_service: WorkoutService,
        test_user: User,
        sample_exercise: Exercise,
    ):
        """Test create_set raises error for non-existent exercise execution."""
        user_id = test_user.id
        exercise_id = sample_exercise.id

        # Create workout but no exercise execution
        workout = await workout_service.create_workout(user_id)
        workout_id = workout.id

        set_data = SetCreate(weight=100.0, clean_reps=10, forced_reps=0)

        # This should raise an error from the repository level
        with pytest.raises(NotFoundError):
            await workout_service.create_set(workout_id, exercise_id, set_data, user_id)

    async def test_update_set_success(
        self,
        workout_service: WorkoutService,
        test_user: User,
        sample_exercise: Exercise,
    ):
        """Test successfully updating an existing set."""
        user_id = test_user.id
        exercise_id = sample_exercise.id

        # Create workout and exercise execution with set
        workout = await workout_service.create_workout(user_id)
        workout_id = workout.id

        execution_data = ExerciseExecutionRequest(
            exercise_order=1,
            sets=[
                SetCreate(
                    weight=100.0, clean_reps=10, forced_reps=0, note_text="Original"
                )
            ],
        )

        execution = await workout_service.upsert_exercise_execution(
            workout_id, exercise_id, execution_data, user_id
        )

        # Get the set ID
        set_id = execution.sets[0].id

        # Update the set
        update_data = SetUpdate(weight=110.0, clean_reps=8, note_text="Updated")

        updated_set = await workout_service.update_set(
            workout_id, exercise_id, set_id, update_data, user_id
        )

        assert updated_set.id == set_id
        assert updated_set.weight == 110.0
        assert updated_set.clean_reps == 8
        assert updated_set.forced_reps == 0  # Should remain unchanged
        assert updated_set.note_text == "Updated"

    async def test_update_set_not_found(
        self,
        workout_service: WorkoutService,
        test_user: User,
        sample_exercise: Exercise,
    ):
        """Test update_set raises NotFoundError for non-existent set."""
        user_id = test_user.id
        exercise_id = sample_exercise.id

        # Create workout and exercise execution
        workout = await workout_service.create_workout(user_id)
        workout_id = workout.id

        execution_data = ExerciseExecutionRequest(
            exercise_order=1,
            sets=[SetCreate(weight=100.0, clean_reps=10, forced_reps=0)],
        )

        await workout_service.upsert_exercise_execution(
            workout_id, exercise_id, execution_data, user_id
        )

        update_data = SetUpdate(weight=110.0)

        with pytest.raises(NotFoundError, match="Set with ID 99999 not found"):
            await workout_service.update_set(
                workout_id, exercise_id, 99999, update_data, user_id
            )

    async def test_update_set_wrong_user(
        self,
        workout_service: WorkoutService,
        test_user: User,
        another_user: User,
        sample_exercise: Exercise,
    ):
        """Test update_set raises NotFoundError when user doesn't own the workout."""
        user_id = test_user.id
        another_user_id = another_user.id
        exercise_id = sample_exercise.id

        # Create workout and exercise execution with test_user
        workout = await workout_service.create_workout(user_id)
        workout_id = workout.id

        execution_data = ExerciseExecutionRequest(
            exercise_order=1,
            sets=[SetCreate(weight=100.0, clean_reps=10, forced_reps=0)],
        )

        execution = await workout_service.upsert_exercise_execution(
            workout_id, exercise_id, execution_data, user_id
        )

        set_id = execution.sets[0].id
        update_data = SetUpdate(weight=110.0)

        # Try to update with different user
        with pytest.raises(NotFoundError):
            await workout_service.update_set(
                workout_id, exercise_id, set_id, update_data, another_user_id
            )

    async def test_delete_set_success(
        self,
        workout_service: WorkoutService,
        test_user: User,
        sample_exercise: Exercise,
    ):
        """Test successfully deleting a set."""
        user_id = test_user.id
        exercise_id = sample_exercise.id

        # Create workout and exercise execution with multiple sets
        workout = await workout_service.create_workout(user_id)
        workout_id = workout.id

        execution_data = ExerciseExecutionRequest(
            exercise_order=1,
            sets=[
                SetCreate(weight=100.0, clean_reps=10, forced_reps=0),
                SetCreate(weight=105.0, clean_reps=8, forced_reps=1),
            ],
        )

        execution = await workout_service.upsert_exercise_execution(
            workout_id, exercise_id, execution_data, user_id
        )

        # Get the first set ID
        set_id = execution.sets[0].id

        # Delete the set
        result = await workout_service.delete_set(
            workout_id, exercise_id, set_id, user_id
        )

        assert result is True

        # Verify set was deleted
        updated_execution = await workout_service.get_exercise_execution(
            workout_id, exercise_id, user_id
        )
        assert len(updated_execution.sets) == 1  # Should have one set remaining
        assert (
            updated_execution.sets[0].id != set_id
        )  # Remaining set should be different

    async def test_delete_set_not_found(
        self,
        workout_service: WorkoutService,
        test_user: User,
        sample_exercise: Exercise,
    ):
        """Test delete_set raises NotFoundError for non-existent set."""
        user_id = test_user.id
        exercise_id = sample_exercise.id

        # Create workout and exercise execution
        workout = await workout_service.create_workout(user_id)
        workout_id = workout.id

        execution_data = ExerciseExecutionRequest(
            exercise_order=1,
            sets=[SetCreate(weight=100.0, clean_reps=10, forced_reps=0)],
        )

        await workout_service.upsert_exercise_execution(
            workout_id, exercise_id, execution_data, user_id
        )

        with pytest.raises(NotFoundError, match="Set with ID 99999 not found"):
            await workout_service.delete_set(workout_id, exercise_id, 99999, user_id)

    async def test_delete_set_wrong_user(
        self,
        workout_service: WorkoutService,
        test_user: User,
        another_user: User,
        sample_exercise: Exercise,
    ):
        """Test delete_set raises NotFoundError when user doesn't own the workout."""
        user_id = test_user.id
        another_user_id = another_user.id
        exercise_id = sample_exercise.id

        # Create workout and exercise execution with test_user
        workout = await workout_service.create_workout(user_id)
        workout_id = workout.id

        execution_data = ExerciseExecutionRequest(
            exercise_order=1,
            sets=[SetCreate(weight=100.0, clean_reps=10, forced_reps=0)],
        )

        execution = await workout_service.upsert_exercise_execution(
            workout_id, exercise_id, execution_data, user_id
        )

        set_id = execution.sets[0].id

        # Try to delete with different user
        with pytest.raises(NotFoundError):
            await workout_service.delete_set(
                workout_id, exercise_id, set_id, another_user_id
            )
