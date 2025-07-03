"""Test workout router endpoints integration."""

import pytest
from httpx import AsyncClient

from workout_api.exercises.models import Exercise
from workout_api.users.models import User
from workout_api.workouts.models import Workout

pytestmark = pytest.mark.anyio


class TestWorkoutRouter:
    """Test workout router endpoints with complete HTTP integration."""

    # ===================
    # create_workout tests
    # ===================

    async def test_create_workout_success(
        self, authenticated_client: AsyncClient, test_user: User
    ):
        """Test successful workout creation via HTTP."""
        # Extract user ID early to avoid lazy loading issues
        user_id = test_user.id

        response = await authenticated_client.post("/api/v1/workouts/")

        assert response.status_code == 201
        data = response.json()

        assert data["id"] is not None
        assert data["created_by_user_id"] == user_id
        assert data["updated_by_user_id"] == user_id
        assert data["finished_at"] is None
        assert data["exercise_executions"] == []
        assert "created_at" in data
        assert "updated_at" in data

    async def test_create_workout_without_auth(self, client: AsyncClient):
        """Test creating workout without authentication returns 403."""
        response = await client.post("/api/v1/workouts/")

        assert response.status_code == 403

    async def test_create_workout_response_format(
        self,
        authenticated_client: AsyncClient,
        test_user: User,  # noqa: ARG002
    ):
        """Test that create workout returns proper JSON structure."""
        response = await authenticated_client.post("/api/v1/workouts/")

        assert response.status_code == 201
        assert response.headers["content-type"] == "application/json"

        data = response.json()

        # Verify all expected fields are present
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

        # Verify field types
        assert isinstance(data["id"], int)
        assert isinstance(data["created_by_user_id"], int)
        assert isinstance(data["updated_by_user_id"], int)
        assert data["finished_at"] is None
        assert isinstance(data["exercise_executions"], list)
        assert isinstance(data["created_at"], str)
        assert isinstance(data["updated_at"], str)

    # =====================================
    # upsert_exercise_execution tests
    # =====================================

    async def test_upsert_exercise_execution_create_success(
        self,
        authenticated_client: AsyncClient,
        sample_workout: Workout,
        sample_exercise: Exercise,
        test_user: User,  # noqa: ARG002
    ):
        """Test creating new exercise execution via HTTP."""
        # Extract IDs early to avoid lazy loading issues
        workout_id = sample_workout.id
        exercise_id = sample_exercise.id

        request_data = {
            "exercise_order": 1,
            "note_text": "First exercise of the day",
            "sets": [
                {"weight": 100.0, "clean_reps": 10, "forced_reps": 0},
                {
                    "weight": 100.0,
                    "clean_reps": 8,
                    "forced_reps": 2,
                    "note_text": "Tough set",
                },
            ],
        }

        response = await authenticated_client.put(
            f"/api/v1/workouts/{workout_id}/exercise-executions/{exercise_id}",
            json=request_data,
        )

        assert response.status_code == 200
        data = response.json()

        assert data["exercise_id"] == exercise_id
        assert data["exercise_name"] == "Test Exercise"  # From fixture
        assert data["exercise_order"] == 1
        assert data["note_text"] == "First exercise of the day"
        assert len(data["sets"]) == 2

        # Verify sets
        assert data["sets"][0]["weight"] == 100.0
        assert data["sets"][0]["clean_reps"] == 10
        assert data["sets"][0]["forced_reps"] == 0
        assert data["sets"][0]["note_text"] is None

        assert data["sets"][1]["weight"] == 100.0
        assert data["sets"][1]["clean_reps"] == 8
        assert data["sets"][1]["forced_reps"] == 2
        assert data["sets"][1]["note_text"] == "Tough set"

    async def test_upsert_exercise_execution_update_success(
        self,
        authenticated_client: AsyncClient,
        workout_with_exercises: Workout,
        sample_exercise: Exercise,
        test_user: User,  # noqa: ARG002
    ):
        """Test updating existing exercise execution via HTTP."""
        # Extract IDs early
        workout_id = workout_with_exercises.id
        exercise_id = sample_exercise.id

        # Get initial state to verify it exists
        get_response = await authenticated_client.get(
            f"/api/v1/workouts/{workout_id}/exercise-executions/{exercise_id}"
        )
        assert get_response.status_code == 200
        initial_data = get_response.json()
        assert len(initial_data["sets"]) == 2  # From fixture

        # Update with different sets (complete replacement)
        request_data = {
            "exercise_order": 3,
            "note_text": "Updated notes",
            "sets": [
                {"weight": 120.0, "clean_reps": 8, "forced_reps": 0},
                {"weight": 120.0, "clean_reps": 6, "forced_reps": 1},
                {"weight": 110.0, "clean_reps": 10, "forced_reps": 0},
            ],
        }

        response = await authenticated_client.put(
            f"/api/v1/workouts/{workout_id}/exercise-executions/{exercise_id}",
            json=request_data,
        )

        assert response.status_code == 200
        data = response.json()

        assert data["exercise_id"] == exercise_id
        assert data["exercise_order"] == 3  # Updated
        assert data["note_text"] == "Updated notes"  # Updated
        assert len(data["sets"]) == 3  # Replaced with 3 sets

        # Verify new sets
        assert data["sets"][0]["weight"] == 120.0
        assert data["sets"][1]["weight"] == 120.0
        assert data["sets"][2]["weight"] == 110.0

    async def test_upsert_exercise_execution_without_auth(
        self, client: AsyncClient, sample_workout: Workout, sample_exercise: Exercise
    ):
        """Test upsert without authentication returns 403."""
        # Extract IDs early
        workout_id = sample_workout.id
        exercise_id = sample_exercise.id

        request_data = {
            "exercise_order": 1,
            "sets": [{"weight": 100.0, "clean_reps": 10, "forced_reps": 0}],
        }

        response = await client.put(
            f"/api/v1/workouts/{workout_id}/exercise-executions/{exercise_id}",
            json=request_data,
        )

        assert response.status_code == 403

    async def test_upsert_exercise_execution_invalid_workout_404(
        self,
        authenticated_client: AsyncClient,
        sample_exercise: Exercise,
        test_user: User,  # noqa: ARG002
    ):
        """Test upsert with non-existent workout returns 404."""
        # Extract ID early
        exercise_id = sample_exercise.id

        request_data = {
            "exercise_order": 1,
            "sets": [{"weight": 100.0, "clean_reps": 10, "forced_reps": 0}],
        }

        response = await authenticated_client.put(
            f"/api/v1/workouts/999999/exercise-executions/{exercise_id}",
            json=request_data,
        )

        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    async def test_upsert_exercise_execution_invalid_exercise_404(
        self,
        authenticated_client: AsyncClient,
        sample_workout: Workout,
        test_user: User,  # noqa: ARG002
    ):
        """Test upsert with non-existent exercise returns 404."""
        # Extract ID early
        workout_id = sample_workout.id

        request_data = {
            "exercise_order": 1,
            "sets": [{"weight": 100.0, "clean_reps": 10, "forced_reps": 0}],
        }

        response = await authenticated_client.put(
            f"/api/v1/workouts/{workout_id}/exercise-executions/999999",
            json=request_data,
        )

        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    async def test_upsert_exercise_execution_validation_error(
        self,
        authenticated_client: AsyncClient,
        sample_workout: Workout,
        sample_exercise: Exercise,
        test_user: User,  # noqa: ARG002
    ):
        """Test upsert with invalid data returns 422."""
        # Extract IDs early
        workout_id = sample_workout.id
        exercise_id = sample_exercise.id

        # Invalid data - negative reps
        request_data = {
            "exercise_order": 1,
            "sets": [
                {
                    "weight": -100.0,  # Invalid negative weight
                    "clean_reps": -5,  # Invalid negative reps
                    "forced_reps": 0,
                }
            ],
        }

        response = await authenticated_client.put(
            f"/api/v1/workouts/{workout_id}/exercise-executions/{exercise_id}",
            json=request_data,
        )

        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    async def test_upsert_exercise_execution_empty_sets(
        self,
        authenticated_client: AsyncClient,
        sample_workout: Workout,
        sample_exercise: Exercise,
        test_user: User,  # noqa: ARG002
    ):
        """Test upsert with empty sets array."""
        # Extract IDs early
        workout_id = sample_workout.id
        exercise_id = sample_exercise.id

        request_data = {
            "exercise_order": 1,
            "note_text": "Exercise with no sets yet",
            "sets": [],  # Empty sets
        }

        response = await authenticated_client.put(
            f"/api/v1/workouts/{workout_id}/exercise-executions/{exercise_id}",
            json=request_data,
        )

        assert response.status_code == 200
        data = response.json()

        assert data["exercise_id"] == exercise_id
        assert data["exercise_order"] == 1
        assert data["note_text"] == "Exercise with no sets yet"
        assert data["sets"] == []

    async def test_upsert_exercise_execution_malformed_json(
        self,
        authenticated_client: AsyncClient,
        sample_workout: Workout,
        sample_exercise: Exercise,
        test_user: User,  # noqa: ARG002
    ):
        """Test upsert with malformed JSON returns 422."""
        # Extract IDs early
        workout_id = sample_workout.id
        exercise_id = sample_exercise.id

        # Send malformed JSON
        response = await authenticated_client.put(
            f"/api/v1/workouts/{workout_id}/exercise-executions/{exercise_id}",
            content='{"invalid": json}',  # Malformed JSON
            headers={"Content-Type": "application/json"},
        )

        assert response.status_code == 422

    async def test_upsert_exercise_execution_missing_required_fields(
        self,
        authenticated_client: AsyncClient,
        sample_workout: Workout,
        sample_exercise: Exercise,
        test_user: User,  # noqa: ARG002
    ):
        """Test upsert with missing required fields returns 422."""
        # Extract IDs early
        workout_id = sample_workout.id
        exercise_id = sample_exercise.id

        # Missing required exercise_order field
        request_data = {
            "sets": [{"weight": 100.0, "clean_reps": 10, "forced_reps": 0}],
            # exercise_order is missing
        }

        response = await authenticated_client.put(
            f"/api/v1/workouts/{workout_id}/exercise-executions/{exercise_id}",
            json=request_data,
        )

        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    async def test_upsert_exercise_execution_user_ownership(
        self,
        another_authenticated_client: AsyncClient,
        sample_workout: Workout,  # Owned by test_user
        sample_exercise: Exercise,
    ):
        """Test that upsert respects user ownership via HTTP."""
        # Extract IDs early
        workout_id = sample_workout.id  # Owned by test_user
        exercise_id = sample_exercise.id

        request_data = {
            "exercise_order": 1,
            "sets": [{"weight": 100.0, "clean_reps": 10, "forced_reps": 0}],
        }

        # another_authenticated_client is authenticated as another_user
        response = await another_authenticated_client.put(
            f"/api/v1/workouts/{workout_id}/exercise-executions/{exercise_id}",
            json=request_data,
        )

        # Should return 404 (not 403) because the workout doesn't exist for this user
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    async def test_upsert_exercise_execution_response_format(
        self,
        authenticated_client: AsyncClient,
        sample_workout: Workout,
        sample_exercise: Exercise,
        test_user: User,  # noqa: ARG002
    ):
        """Test that upsert returns proper JSON structure."""
        # Extract IDs early
        workout_id = sample_workout.id
        exercise_id = sample_exercise.id

        request_data = {
            "exercise_order": 1,
            "note_text": "Test notes",
            "sets": [
                {
                    "weight": 100.0,
                    "clean_reps": 10,
                    "forced_reps": 0,
                    "note_text": "Set notes",
                }
            ],
        }

        response = await authenticated_client.put(
            f"/api/v1/workouts/{workout_id}/exercise-executions/{exercise_id}",
            json=request_data,
        )

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"

        data = response.json()

        # Verify exercise execution fields
        execution_expected_fields = {
            "exercise_id",
            "exercise_name",
            "exercise_order",
            "note_text",
            "sets",
            "created_at",
            "updated_at",
        }
        assert execution_expected_fields.issubset(data.keys())

        # Verify field types
        assert isinstance(data["exercise_id"], int)
        assert isinstance(data["exercise_name"], str)
        assert isinstance(data["exercise_order"], int)
        assert isinstance(data["sets"], list)
        assert isinstance(data["created_at"], str)
        assert isinstance(data["updated_at"], str)

        # Verify set structure
        assert len(data["sets"]) == 1
        set_data = data["sets"][0]
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

        # Verify set field types
        assert isinstance(set_data["id"], int)
        assert isinstance(set_data["weight"], int | float)
        assert isinstance(set_data["clean_reps"], int)
        assert isinstance(set_data["forced_reps"], int)
        assert isinstance(set_data["created_at"], str)
        assert isinstance(set_data["updated_at"], str)
