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

    # ===================
    # list_workouts tests
    # ===================

    async def test_list_workouts_success_no_filters(
        self,
        authenticated_client: AsyncClient,
        test_user: User,  # noqa: ARG002
    ):
        """Test successful workout listing with no filters."""
        response = await authenticated_client.get("/api/v1/workouts/")

        assert response.status_code == 200
        data = response.json()

        # Verify pagination structure
        assert "items" in data
        assert "page" in data
        assert "size" in data
        assert "total" in data
        assert "pages" in data

        assert isinstance(data["items"], list)
        assert data["page"] == 1
        assert data["size"] == 20  # Default size

    async def test_list_workouts_with_pagination(
        self,
        authenticated_client: AsyncClient,
        test_user: User,  # noqa: ARG002
    ):
        """Test workout listing with custom pagination."""
        response = await authenticated_client.get("/api/v1/workouts/?page=1&size=5")

        assert response.status_code == 200
        data = response.json()

        assert data["page"] == 1
        assert data["size"] == 5

    async def test_list_workouts_with_date_filters(
        self,
        authenticated_client: AsyncClient,
        test_user: User,  # noqa: ARG002
    ):
        """Test workout listing with date filters."""
        response = await authenticated_client.get(
            "/api/v1/workouts/?start_date=2024-01-01T00:00:00Z&end_date=2024-12-31T23:59:59Z"
        )

        assert response.status_code == 200
        data = response.json()
        assert "items" in data

    async def test_list_workouts_with_finished_filter(
        self,
        authenticated_client: AsyncClient,
        test_user: User,  # noqa: ARG002
    ):
        """Test workout listing with finished filter."""
        response = await authenticated_client.get("/api/v1/workouts/?finished=true")

        assert response.status_code == 200
        data = response.json()
        assert "items" in data

        response = await authenticated_client.get("/api/v1/workouts/?finished=false")

        assert response.status_code == 200
        data = response.json()
        assert "items" in data

    async def test_list_workouts_invalid_date_format(
        self,
        authenticated_client: AsyncClient,
        test_user: User,  # noqa: ARG002
    ):
        """Test workout listing with invalid date format returns 422."""
        response = await authenticated_client.get(
            "/api/v1/workouts/?start_date=invalid-date"
        )

        assert response.status_code == 422
        data = response.json()
        assert "Invalid date format" in data["detail"]

    async def test_list_workouts_without_auth(self, client: AsyncClient):
        """Test listing workouts without authentication returns 403."""
        response = await client.get("/api/v1/workouts/")

        assert response.status_code == 403

    async def test_list_workouts_response_format(
        self,
        authenticated_client: AsyncClient,
        sample_workout: Workout,  # noqa: ARG002
        test_user: User,  # noqa: ARG002
    ):
        """Test that list workouts returns proper JSON structure."""
        response = await authenticated_client.get("/api/v1/workouts/")

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"

        data = response.json()

        # Verify pagination fields
        pagination_fields = {"items", "page", "size", "total", "pages"}
        assert pagination_fields.issubset(data.keys())

        # If there are items, verify workout structure
        if data["items"]:
            workout_data = data["items"][0]
            workout_expected_fields = {
                "id",
                "created_by_user_id",
                "updated_by_user_id",
                "finished_at",
                "exercise_executions",
                "created_at",
                "updated_at",
            }
            assert workout_expected_fields.issubset(workout_data.keys())

    # ==================
    # get_workout tests
    # ==================

    async def test_get_workout_success(
        self,
        authenticated_client: AsyncClient,
        sample_workout: Workout,
        test_user: User,  # noqa: ARG002
    ):
        """Test successful retrieval of a single workout."""
        workout_id = sample_workout.id

        response = await authenticated_client.get(f"/api/v1/workouts/{workout_id}")

        assert response.status_code == 200
        data = response.json()

        assert data["id"] == workout_id
        assert "created_by_user_id" in data
        assert "updated_by_user_id" in data
        assert "exercise_executions" in data
        assert "created_at" in data
        assert "updated_at" in data

    async def test_get_workout_not_found(
        self,
        authenticated_client: AsyncClient,
        test_user: User,  # noqa: ARG002
    ):
        """Test getting non-existent workout returns 404."""
        response = await authenticated_client.get("/api/v1/workouts/99999")

        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    async def test_get_workout_user_ownership(
        self,
        another_authenticated_client: AsyncClient,
        sample_workout: Workout,  # Owned by test_user
    ):
        """Test that get workout respects user ownership."""
        workout_id = sample_workout.id

        response = await another_authenticated_client.get(
            f"/api/v1/workouts/{workout_id}"
        )

        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    async def test_get_workout_without_auth(
        self, client: AsyncClient, sample_workout: Workout
    ):
        """Test getting workout without authentication returns 403."""
        workout_id = sample_workout.id

        response = await client.get(f"/api/v1/workouts/{workout_id}")

        assert response.status_code == 403

    async def test_get_workout_with_exercises(
        self,
        authenticated_client: AsyncClient,
        workout_with_exercises: Workout,
        test_user: User,  # noqa: ARG002
    ):
        """Test getting workout with exercise executions."""
        workout_id = workout_with_exercises.id

        response = await authenticated_client.get(f"/api/v1/workouts/{workout_id}")

        assert response.status_code == 200
        data = response.json()

        assert data["id"] == workout_id
        assert isinstance(data["exercise_executions"], list)
        assert len(data["exercise_executions"]) > 0

        # Verify exercise execution structure
        execution = data["exercise_executions"][0]
        execution_expected_fields = {
            "exercise_id",
            "exercise_name",
            "exercise_order",
            "sets",
        }
        assert execution_expected_fields.issubset(execution.keys())

    # =====================
    # finish_workout tests
    # =====================

    async def test_finish_workout_success(
        self,
        authenticated_client: AsyncClient,
        sample_workout: Workout,
        test_user: User,  # noqa: ARG002
    ):
        """Test successfully finishing an active workout."""
        workout_id = sample_workout.id

        response = await authenticated_client.patch(
            f"/api/v1/workouts/{workout_id}/finish"
        )

        assert response.status_code == 200
        data = response.json()

        assert data["id"] == workout_id
        assert data["finished_at"] is not None
        # Verify timestamp format
        assert isinstance(data["finished_at"], str)

    async def test_finish_workout_not_found(
        self,
        authenticated_client: AsyncClient,
        test_user: User,  # noqa: ARG002
    ):
        """Test finishing non-existent workout returns 404."""
        response = await authenticated_client.patch("/api/v1/workouts/99999/finish")

        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    async def test_finish_workout_already_finished(
        self,
        authenticated_client: AsyncClient,
        finished_workout: Workout,
        test_user: User,  # noqa: ARG002
    ):
        """Test finishing already finished workout returns 400."""
        workout_id = finished_workout.id

        response = await authenticated_client.patch(
            f"/api/v1/workouts/{workout_id}/finish"
        )

        assert response.status_code == 400
        data = response.json()
        assert "already finished" in data["detail"].lower()

    async def test_finish_workout_user_ownership(
        self,
        another_authenticated_client: AsyncClient,
        sample_workout: Workout,  # Owned by test_user
    ):
        """Test that finish workout respects user ownership."""
        workout_id = sample_workout.id

        response = await another_authenticated_client.patch(
            f"/api/v1/workouts/{workout_id}/finish"
        )

        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    async def test_finish_workout_without_auth(
        self, client: AsyncClient, sample_workout: Workout
    ):
        """Test finishing workout without authentication returns 403."""
        workout_id = sample_workout.id

        response = await client.patch(f"/api/v1/workouts/{workout_id}/finish")

        assert response.status_code == 403

    # =====================
    # delete_workout tests
    # =====================

    async def test_delete_workout_success(
        self,
        authenticated_client: AsyncClient,
        sample_workout: Workout,
        test_user: User,  # noqa: ARG002
    ):
        """Test successfully deleting a workout."""
        # Extract workout_id early to avoid lazy loading
        workout_id = sample_workout.id

        response = await authenticated_client.delete(f"/api/v1/workouts/{workout_id}")

        assert response.status_code == 204
        assert response.content == b""

        # Verify workout is deleted by trying to get it
        get_response = await authenticated_client.get(f"/api/v1/workouts/{workout_id}")
        assert get_response.status_code == 404

    async def test_delete_workout_not_found(
        self,
        authenticated_client: AsyncClient,
        test_user: User,  # noqa: ARG002
    ):
        """Test deleting non-existent workout returns 404."""
        response = await authenticated_client.delete("/api/v1/workouts/99999")

        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    async def test_delete_workout_user_ownership(
        self,
        another_authenticated_client: AsyncClient,
        sample_workout: Workout,  # Owned by test_user
    ):
        """Test that delete workout respects user ownership."""
        workout_id = sample_workout.id

        response = await another_authenticated_client.delete(
            f"/api/v1/workouts/{workout_id}"
        )

        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    async def test_delete_workout_without_auth(
        self, client: AsyncClient, sample_workout: Workout
    ):
        """Test deleting workout without authentication returns 403."""
        workout_id = sample_workout.id

        response = await client.delete(f"/api/v1/workouts/{workout_id}")

        assert response.status_code == 403

    async def test_delete_workout_with_exercises(
        self,
        authenticated_client: AsyncClient,
        workout_with_exercises: Workout,
        test_user: User,  # noqa: ARG002
    ):
        """Test deleting workout with exercise executions and sets."""
        # Extract workout_id early to avoid lazy loading issues
        workout_id = workout_with_exercises.id

        response = await authenticated_client.delete(f"/api/v1/workouts/{workout_id}")

        assert response.status_code == 204

        # Verify workout and related data is deleted
        get_response = await authenticated_client.get(f"/api/v1/workouts/{workout_id}")
        assert get_response.status_code == 404

    # ==============================
    # get_exercise_execution tests
    # ==============================

    async def test_get_exercise_execution_success(
        self,
        authenticated_client: AsyncClient,
        workout_with_exercises: Workout,
        sample_exercise: Exercise,
        test_user: User,  # noqa: ARG002
    ):
        """Test successfully getting exercise execution with sets."""
        workout_id = workout_with_exercises.id
        exercise_id = sample_exercise.id

        response = await authenticated_client.get(
            f"/api/v1/workouts/{workout_id}/exercise-executions/{exercise_id}"
        )

        assert response.status_code == 200
        data = response.json()

        assert data["exercise_id"] == exercise_id
        assert "exercise_name" in data
        assert "exercise_order" in data
        assert "sets" in data
        assert isinstance(data["sets"], list)

    async def test_get_exercise_execution_not_found(
        self,
        authenticated_client: AsyncClient,
        sample_workout: Workout,
        sample_exercise: Exercise,
        test_user: User,  # noqa: ARG002
    ):
        """Test getting non-existent exercise execution returns 404."""
        workout_id = sample_workout.id
        exercise_id = sample_exercise.id

        response = await authenticated_client.get(
            f"/api/v1/workouts/{workout_id}/exercise-executions/{exercise_id}"
        )

        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    async def test_get_exercise_execution_user_ownership(
        self,
        another_authenticated_client: AsyncClient,
        workout_with_exercises: Workout,  # Owned by test_user
        sample_exercise: Exercise,
    ):
        """Test that get exercise execution respects user ownership."""
        workout_id = workout_with_exercises.id
        exercise_id = sample_exercise.id

        response = await another_authenticated_client.get(
            f"/api/v1/workouts/{workout_id}/exercise-executions/{exercise_id}"
        )

        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    async def test_get_exercise_execution_without_auth(
        self,
        client: AsyncClient,
        workout_with_exercises: Workout,
        sample_exercise: Exercise,
    ):
        """Test getting exercise execution without authentication returns 403."""
        workout_id = workout_with_exercises.id
        exercise_id = sample_exercise.id

        response = await client.get(
            f"/api/v1/workouts/{workout_id}/exercise-executions/{exercise_id}"
        )

        assert response.status_code == 403

    # =================================
    # delete_exercise_execution tests
    # =================================

    async def test_delete_exercise_execution_success(
        self,
        authenticated_client: AsyncClient,
        workout_with_exercises: Workout,
        sample_exercise: Exercise,
        test_user: User,  # noqa: ARG002
    ):
        """Test successfully deleting exercise execution."""
        # Extract IDs early to avoid lazy loading issues
        workout_id = workout_with_exercises.id
        exercise_id = sample_exercise.id

        response = await authenticated_client.delete(
            f"/api/v1/workouts/{workout_id}/exercise-executions/{exercise_id}"
        )

        assert response.status_code == 204
        assert response.content == b""

        # Verify exercise execution is deleted
        get_response = await authenticated_client.get(
            f"/api/v1/workouts/{workout_id}/exercise-executions/{exercise_id}"
        )
        assert get_response.status_code == 404

    async def test_delete_exercise_execution_not_found(
        self,
        authenticated_client: AsyncClient,
        sample_workout: Workout,
        sample_exercise: Exercise,
        test_user: User,  # noqa: ARG002
    ):
        """Test deleting non-existent exercise execution returns 404."""
        workout_id = sample_workout.id
        exercise_id = sample_exercise.id

        response = await authenticated_client.delete(
            f"/api/v1/workouts/{workout_id}/exercise-executions/{exercise_id}"
        )

        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    async def test_delete_exercise_execution_finished_workout(
        self,
        authenticated_client: AsyncClient,
        sample_workout: Workout,
        sample_exercise: Exercise,
        test_user: User,  # noqa: ARG002
    ):
        """Test deleting exercise execution from finished workout returns 400."""
        workout_id = sample_workout.id
        exercise_id = sample_exercise.id

        # First add an exercise execution to the active workout
        await authenticated_client.put(
            f"/api/v1/workouts/{workout_id}/exercise-executions/{exercise_id}",
            json={"exercise_order": 1, "sets": []},
        )

        # Finish the workout
        await authenticated_client.patch(f"/api/v1/workouts/{workout_id}/finish")

        # Now try to delete exercise execution from finished workout
        response = await authenticated_client.delete(
            f"/api/v1/workouts/{workout_id}/exercise-executions/{exercise_id}"
        )

        assert response.status_code == 400
        data = response.json()
        assert "cannot modify finished workout" in data["detail"].lower()

    async def test_delete_exercise_execution_user_ownership(
        self,
        another_authenticated_client: AsyncClient,
        workout_with_exercises: Workout,  # Owned by test_user
        sample_exercise: Exercise,
    ):
        """Test that delete exercise execution respects user ownership."""
        workout_id = workout_with_exercises.id
        exercise_id = sample_exercise.id

        response = await another_authenticated_client.delete(
            f"/api/v1/workouts/{workout_id}/exercise-executions/{exercise_id}"
        )

        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    # =================================
    # update_exercise_execution tests
    # =================================

    async def test_update_exercise_execution_success(
        self,
        authenticated_client: AsyncClient,
        workout_with_exercises: Workout,
        sample_exercise: Exercise,
        test_user: User,  # noqa: ARG002
    ):
        """Test successfully updating exercise execution metadata."""
        workout_id = workout_with_exercises.id
        exercise_id = sample_exercise.id

        update_data = {
            "exercise_order": 5,
            "note_text": "Updated notes for this exercise",
        }

        response = await authenticated_client.patch(
            f"/api/v1/workouts/{workout_id}/exercise-executions/{exercise_id}",
            json=update_data,
        )

        assert response.status_code == 200
        data = response.json()

        assert data["exercise_id"] == exercise_id
        assert data["exercise_order"] == 5
        assert data["note_text"] == "Updated notes for this exercise"

    async def test_update_exercise_execution_not_found(
        self,
        authenticated_client: AsyncClient,
        sample_workout: Workout,
        sample_exercise: Exercise,
        test_user: User,  # noqa: ARG002
    ):
        """Test updating non-existent exercise execution returns 404."""
        workout_id = sample_workout.id
        exercise_id = sample_exercise.id

        update_data = {"exercise_order": 5}

        response = await authenticated_client.patch(
            f"/api/v1/workouts/{workout_id}/exercise-executions/{exercise_id}",
            json=update_data,
        )

        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    async def test_update_exercise_execution_finished_workout(
        self,
        authenticated_client: AsyncClient,
        sample_workout: Workout,
        sample_exercise: Exercise,
        test_user: User,  # noqa: ARG002
    ):
        """Test updating exercise execution in finished workout returns 400."""
        workout_id = sample_workout.id
        exercise_id = sample_exercise.id

        # First add an exercise execution to the active workout
        await authenticated_client.put(
            f"/api/v1/workouts/{workout_id}/exercise-executions/{exercise_id}",
            json={"exercise_order": 1, "sets": []},
        )

        # Finish the workout
        await authenticated_client.patch(f"/api/v1/workouts/{workout_id}/finish")

        update_data = {"exercise_order": 5}

        response = await authenticated_client.patch(
            f"/api/v1/workouts/{workout_id}/exercise-executions/{exercise_id}",
            json=update_data,
        )

        assert response.status_code == 400
        data = response.json()
        assert "cannot modify finished workout" in data["detail"].lower()

    # ========================
    # reorder_exercises tests
    # ========================

    async def test_reorder_exercises_success(
        self,
        authenticated_client: AsyncClient,
        workout_with_exercises: Workout,
        sample_exercise: Exercise,
        another_exercise: Exercise,
        test_user: User,  # noqa: ARG002
    ):
        """Test successfully reordering exercises."""
        workout_id = workout_with_exercises.id
        sample_exercise_id = sample_exercise.id
        another_exercise_id = another_exercise.id

        reorder_data = {"exercise_ids": [another_exercise_id, sample_exercise_id]}

        response = await authenticated_client.patch(
            f"/api/v1/workouts/{workout_id}/exercise-executions/reorder",
            json=reorder_data,
        )

        assert response.status_code == 200
        data = response.json()

        assert "exercise_executions" in data
        assert len(data["exercise_executions"]) == 2

        # Verify order changed (another_exercise should be first now)
        first_execution = data["exercise_executions"][0]
        second_execution = data["exercise_executions"][1]

        assert first_execution["exercise_id"] == another_exercise_id
        assert second_execution["exercise_id"] == sample_exercise_id

    async def test_reorder_exercises_not_found(
        self,
        authenticated_client: AsyncClient,
        test_user: User,  # noqa: ARG002
    ):
        """Test reordering exercises for non-existent workout returns 404."""
        reorder_data = {"exercise_ids": [1, 2]}

        response = await authenticated_client.patch(
            "/api/v1/workouts/99999/exercise-executions/reorder",
            json=reorder_data,
        )

        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    async def test_reorder_exercises_mismatch(
        self,
        authenticated_client: AsyncClient,
        workout_with_exercises: Workout,
        test_user: User,  # noqa: ARG002
    ):
        """Test reordering exercises with mismatched IDs returns 400."""
        workout_id = workout_with_exercises.id

        # Provide wrong exercise IDs
        reorder_data = {"exercise_ids": [99999, 88888]}

        response = await authenticated_client.patch(
            f"/api/v1/workouts/{workout_id}/exercise-executions/reorder",
            json=reorder_data,
        )

        assert response.status_code == 400
        data = response.json()
        assert "mismatch" in data["detail"].lower()

    async def test_reorder_exercises_finished_workout(
        self,
        authenticated_client: AsyncClient,
        sample_workout: Workout,
        sample_exercise: Exercise,
        test_user: User,  # noqa: ARG002
    ):
        """Test reordering exercises in finished workout returns 400."""
        workout_id = sample_workout.id
        exercise_id = sample_exercise.id

        # First add an exercise execution to the active workout
        await authenticated_client.put(
            f"/api/v1/workouts/{workout_id}/exercise-executions/{exercise_id}",
            json={"exercise_order": 1, "sets": []},
        )

        # Finish the workout
        await authenticated_client.patch(f"/api/v1/workouts/{workout_id}/finish")

        reorder_data = {"exercise_ids": [exercise_id]}

        response = await authenticated_client.patch(
            f"/api/v1/workouts/{workout_id}/exercise-executions/reorder",
            json=reorder_data,
        )

        assert response.status_code == 400
        data = response.json()
        assert "cannot modify finished workout" in data["detail"].lower()

    # ==================
    # create_set tests
    # ==================

    async def test_create_set_success(
        self,
        authenticated_client: AsyncClient,
        workout_with_exercises: Workout,
        sample_exercise: Exercise,
        test_user: User,  # noqa: ARG002
    ):
        """Test successfully creating a new set."""
        workout_id = workout_with_exercises.id
        exercise_id = sample_exercise.id

        set_data = {
            "weight": 150.0,
            "clean_reps": 8,
            "forced_reps": 2,
            "note_text": "Great set!",
        }

        response = await authenticated_client.post(
            f"/api/v1/workouts/{workout_id}/exercise-executions/{exercise_id}/sets",
            json=set_data,
        )

        assert response.status_code == 201
        data = response.json()

        assert data["weight"] == 150.0
        assert data["clean_reps"] == 8
        assert data["forced_reps"] == 2
        assert data["note_text"] == "Great set!"
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data

    async def test_create_set_exercise_not_found(
        self,
        authenticated_client: AsyncClient,
        sample_workout: Workout,
        sample_exercise: Exercise,
        test_user: User,  # noqa: ARG002
    ):
        """Test creating set for non-existent exercise execution returns 404."""
        workout_id = sample_workout.id
        exercise_id = sample_exercise.id

        set_data = {
            "weight": 150.0,
            "clean_reps": 8,
            "forced_reps": 0,
        }

        response = await authenticated_client.post(
            f"/api/v1/workouts/{workout_id}/exercise-executions/{exercise_id}/sets",
            json=set_data,
        )

        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    async def test_create_set_finished_workout(
        self,
        authenticated_client: AsyncClient,
        sample_workout: Workout,
        sample_exercise: Exercise,
        test_user: User,  # noqa: ARG002
    ):
        """Test creating set in finished workout returns 400."""
        workout_id = sample_workout.id
        exercise_id = sample_exercise.id

        # First add an exercise execution to the active workout
        await authenticated_client.put(
            f"/api/v1/workouts/{workout_id}/exercise-executions/{exercise_id}",
            json={"exercise_order": 1, "sets": []},
        )

        # Finish the workout
        await authenticated_client.patch(f"/api/v1/workouts/{workout_id}/finish")

        set_data = {
            "weight": 150.0,
            "clean_reps": 8,
            "forced_reps": 0,
        }

        response = await authenticated_client.post(
            f"/api/v1/workouts/{workout_id}/exercise-executions/{exercise_id}/sets",
            json=set_data,
        )

        assert response.status_code == 400
        data = response.json()
        assert "cannot modify finished workout" in data["detail"].lower()

    async def test_create_set_validation_error(
        self,
        authenticated_client: AsyncClient,
        workout_with_exercises: Workout,
        sample_exercise: Exercise,
        test_user: User,  # noqa: ARG002
    ):
        """Test creating set with invalid data returns 422."""
        workout_id = workout_with_exercises.id
        exercise_id = sample_exercise.id

        set_data = {
            "weight": -150.0,  # Invalid negative weight
            "clean_reps": -8,  # Invalid negative reps
            "forced_reps": 0,
        }

        response = await authenticated_client.post(
            f"/api/v1/workouts/{workout_id}/exercise-executions/{exercise_id}/sets",
            json=set_data,
        )

        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    async def test_create_set_user_ownership(
        self,
        another_authenticated_client: AsyncClient,
        workout_with_exercises: Workout,  # Owned by test_user
        sample_exercise: Exercise,
    ):
        """Test that create set respects user ownership."""
        workout_id = workout_with_exercises.id
        exercise_id = sample_exercise.id

        set_data = {
            "weight": 150.0,
            "clean_reps": 8,
            "forced_reps": 0,
        }

        response = await another_authenticated_client.post(
            f"/api/v1/workouts/{workout_id}/exercise-executions/{exercise_id}/sets",
            json=set_data,
        )

        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    # ==================
    # update_set tests
    # ==================

    async def test_update_set_success(
        self,
        authenticated_client: AsyncClient,
        workout_with_exercises: Workout,
        sample_exercise: Exercise,
        test_user: User,  # noqa: ARG002
    ):
        """Test successfully updating a set."""
        workout_id = workout_with_exercises.id
        exercise_id = sample_exercise.id

        # First get existing sets to find a set ID
        get_response = await authenticated_client.get(
            f"/api/v1/workouts/{workout_id}/exercise-executions/{exercise_id}"
        )
        existing_sets = get_response.json()["sets"]
        assert len(existing_sets) > 0
        set_id = existing_sets[0]["id"]

        update_data = {
            "weight": 175.0,
            "clean_reps": 6,
            "forced_reps": 3,
            "note_text": "Updated set notes",
        }

        response = await authenticated_client.patch(
            f"/api/v1/workouts/{workout_id}/exercise-executions/{exercise_id}/sets/{set_id}",
            json=update_data,
        )

        assert response.status_code == 200
        data = response.json()

        assert data["id"] == set_id
        assert data["weight"] == 175.0
        assert data["clean_reps"] == 6
        assert data["forced_reps"] == 3
        assert data["note_text"] == "Updated set notes"

    async def test_update_set_not_found(
        self,
        authenticated_client: AsyncClient,
        workout_with_exercises: Workout,
        sample_exercise: Exercise,
        test_user: User,  # noqa: ARG002
    ):
        """Test updating non-existent set returns 404."""
        workout_id = workout_with_exercises.id
        exercise_id = sample_exercise.id

        update_data = {"weight": 175.0}

        response = await authenticated_client.patch(
            f"/api/v1/workouts/{workout_id}/exercise-executions/{exercise_id}/sets/99999",
            json=update_data,
        )

        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    async def test_update_set_finished_workout(
        self,
        authenticated_client: AsyncClient,
        sample_workout: Workout,
        sample_exercise: Exercise,
        test_user: User,  # noqa: ARG002
    ):
        """Test updating set in finished workout returns 400."""
        workout_id = sample_workout.id
        exercise_id = sample_exercise.id

        # First add an exercise execution with a set to the active workout
        await authenticated_client.put(
            f"/api/v1/workouts/{workout_id}/exercise-executions/{exercise_id}",
            json={
                "exercise_order": 1,
                "sets": [{"weight": 100.0, "clean_reps": 10, "forced_reps": 0}],
            },
        )

        # Get the set ID before finishing workout
        get_response = await authenticated_client.get(
            f"/api/v1/workouts/{workout_id}/exercise-executions/{exercise_id}"
        )
        sets = get_response.json()["sets"]
        set_id = sets[0]["id"]

        # Finish the workout
        await authenticated_client.patch(f"/api/v1/workouts/{workout_id}/finish")

        update_data = {"weight": 175.0}

        response = await authenticated_client.patch(
            f"/api/v1/workouts/{workout_id}/exercise-executions/{exercise_id}/sets/{set_id}",
            json=update_data,
        )

        assert response.status_code == 400
        data = response.json()
        assert "cannot modify finished workout" in data["detail"].lower()

    async def test_update_set_validation_error(
        self,
        authenticated_client: AsyncClient,
        workout_with_exercises: Workout,
        sample_exercise: Exercise,
        test_user: User,  # noqa: ARG002
    ):
        """Test updating set with invalid data returns 422."""
        workout_id = workout_with_exercises.id
        exercise_id = sample_exercise.id

        # Get existing set ID
        get_response = await authenticated_client.get(
            f"/api/v1/workouts/{workout_id}/exercise-executions/{exercise_id}"
        )
        existing_sets = get_response.json()["sets"]
        set_id = existing_sets[0]["id"]

        update_data = {
            "weight": -175.0,  # Invalid negative weight
            "clean_reps": -6,  # Invalid negative reps
        }

        response = await authenticated_client.patch(
            f"/api/v1/workouts/{workout_id}/exercise-executions/{exercise_id}/sets/{set_id}",
            json=update_data,
        )

        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    # ==================
    # delete_set tests
    # ==================

    async def test_delete_set_success(
        self,
        authenticated_client: AsyncClient,
        workout_with_exercises: Workout,
        sample_exercise: Exercise,
        test_user: User,  # noqa: ARG002
    ):
        """Test successfully deleting a set."""
        # Extract IDs early to avoid lazy loading issues
        workout_id = workout_with_exercises.id
        exercise_id = sample_exercise.id

        # Get existing set ID
        get_response = await authenticated_client.get(
            f"/api/v1/workouts/{workout_id}/exercise-executions/{exercise_id}"
        )
        existing_sets = get_response.json()["sets"]
        assert len(existing_sets) > 0
        set_id = existing_sets[0]["id"]

        response = await authenticated_client.delete(
            f"/api/v1/workouts/{workout_id}/exercise-executions/{exercise_id}/sets/{set_id}"
        )

        assert response.status_code == 204
        assert response.content == b""

        # Verify set is deleted
        get_response_after = await authenticated_client.get(
            f"/api/v1/workouts/{workout_id}/exercise-executions/{exercise_id}"
        )
        remaining_sets = get_response_after.json()["sets"]
        set_ids = [s["id"] for s in remaining_sets]
        assert set_id not in set_ids

    async def test_delete_set_not_found(
        self,
        authenticated_client: AsyncClient,
        workout_with_exercises: Workout,
        sample_exercise: Exercise,
        test_user: User,  # noqa: ARG002
    ):
        """Test deleting non-existent set returns 404."""
        workout_id = workout_with_exercises.id
        exercise_id = sample_exercise.id

        response = await authenticated_client.delete(
            f"/api/v1/workouts/{workout_id}/exercise-executions/{exercise_id}/sets/99999"
        )

        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    async def test_delete_set_finished_workout(
        self,
        authenticated_client: AsyncClient,
        sample_workout: Workout,
        sample_exercise: Exercise,
        test_user: User,  # noqa: ARG002
    ):
        """Test deleting set from finished workout returns 400."""
        workout_id = sample_workout.id
        exercise_id = sample_exercise.id

        # First add an exercise execution with a set to the active workout
        await authenticated_client.put(
            f"/api/v1/workouts/{workout_id}/exercise-executions/{exercise_id}",
            json={
                "exercise_order": 1,
                "sets": [{"weight": 100.0, "clean_reps": 10, "forced_reps": 0}],
            },
        )

        # Get the set ID before finishing workout
        get_response = await authenticated_client.get(
            f"/api/v1/workouts/{workout_id}/exercise-executions/{exercise_id}"
        )
        sets = get_response.json()["sets"]
        set_id = sets[0]["id"]

        # Finish the workout
        await authenticated_client.patch(f"/api/v1/workouts/{workout_id}/finish")

        response = await authenticated_client.delete(
            f"/api/v1/workouts/{workout_id}/exercise-executions/{exercise_id}/sets/{set_id}"
        )

        assert response.status_code == 400
        data = response.json()
        assert "cannot modify finished workout" in data["detail"].lower()

    async def test_delete_set_user_ownership(
        self,
        another_authenticated_client: AsyncClient,
        workout_with_exercises: Workout,  # Owned by test_user
        sample_exercise: Exercise,
    ):
        """Test that delete set respects user ownership."""
        workout_id = workout_with_exercises.id
        exercise_id = sample_exercise.id

        response = await another_authenticated_client.delete(
            f"/api/v1/workouts/{workout_id}/exercise-executions/{exercise_id}/sets/1"
        )

        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()
