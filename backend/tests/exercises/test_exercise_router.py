"""Test exercise router endpoints."""

import pytest
from httpx import AsyncClient

from workout_api.exercises.models import Exercise, ExerciseModality
from workout_api.users.models import User

# Mark all tests in this module as anyio tests
pytestmark = pytest.mark.anyio


class TestExerciseRouter:
    """Test exercise router endpoints."""

    async def test_search_exercises_public(
        self,
        client: AsyncClient,
        multiple_exercises,  # noqa: ARG002
    ):
        """Test public exercise search without authentication."""
        response = await client.get("/api/v1/exercises/")

        assert response.status_code == 200
        data = response.json()

        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "size" in data
        assert data["total"] >= len(multiple_exercises)

    async def test_search_exercises_with_filters(
        self,
        client: AsyncClient,
        multiple_exercises,  # noqa: ARG002
    ):
        """Test exercise search with query filters."""
        response = await client.get(
            "/api/v1/exercises/",
            params={
                "name": "User",
                "body_part": "Chest",
                "modality": "DUMBBELL",
                "page": 1,
                "size": 5,
            },
        )

        assert response.status_code == 200
        data = response.json()

        assert data["page"] == 1
        assert data["size"] == 5
        for item in data["items"]:
            # Should match at least one filter
            assert (
                "User" in item["name"]
                or "Chest" in item["body_part"]
                or item["modality"] == "DUMBBELL"
            )

    async def test_search_exercises_pagination(
        self,
        client: AsyncClient,
        multiple_exercises,  # noqa: ARG002
    ):
        """Test exercise search pagination."""
        # First page
        response = await client.get("/api/v1/exercises/", params={"page": 1, "size": 2})

        assert response.status_code == 200
        data = response.json()

        assert data["page"] == 1
        assert data["size"] == 2
        assert len(data["items"]) <= 2

        if data["total"] > 2:
            # Second page
            response2 = await client.get(
                "/api/v1/exercises/", params={"page": 2, "size": 2}
            )

            assert response2.status_code == 200
            data2 = response2.json()
            assert data2["page"] == 2

    async def test_get_exercise_by_id_existing(
        self, client: AsyncClient, system_exercise
    ):
        """Test getting exercise by existing ID."""
        # Extract ID early
        exercise_id = system_exercise.id

        response = await client.get(f"/api/v1/exercises/{exercise_id}")

        assert response.status_code == 200
        data = response.json()

        assert data["id"] == exercise_id
        assert data["name"] == "Barbell Bench Press"
        assert data["is_user_created"] is False

    async def test_get_exercise_by_id_nonexistent(self, client: AsyncClient):
        """Test getting exercise by non-existent ID."""
        response = await client.get("/api/v1/exercises/999999")

        assert response.status_code == 404
        data = response.json()
        assert "Exercise not found" in data["detail"]

    async def test_create_exercise_success(
        self, authenticated_client: AsyncClient, sample_user: User
    ):
        """Test successful exercise creation."""
        # Extract user ID early to avoid lazy loading issues
        user_id = sample_user.id

        exercise_data = {
            "name": "My Custom Exercise",
            "body_part": "Arms",
            "modality": "DUMBBELL",
            "picture_url": "https://example.com/my_exercise.jpg",
        }

        response = await authenticated_client.post(
            "/api/v1/exercises/", json=exercise_data
        )

        assert response.status_code == 201
        data = response.json()

        assert data["name"] == "My Custom Exercise"
        assert data["body_part"] == "Arms"
        assert data["modality"] == "DUMBBELL"
        assert data["picture_url"] == "https://example.com/my_exercise.jpg"
        assert data["is_user_created"] is True
        assert data["created_by_user_id"] == user_id
        assert data["updated_by_user_id"] == user_id

    async def test_create_exercise_validation_error(
        self, authenticated_client: AsyncClient
    ):
        """Test creating exercise with invalid data."""
        exercise_data = {
            "name": "",  # Invalid empty name
            "body_part": "Arms",
            "modality": "INVALID_MODALITY",
        }

        response = await authenticated_client.post(
            "/api/v1/exercises/", json=exercise_data
        )

        assert response.status_code == 422  # Validation error
        data = response.json()
        assert "detail" in data

    async def test_create_exercise_without_auth(self, client: AsyncClient):
        """Test creating exercise without authentication."""
        exercise_data = {
            "name": "Test Exercise",
            "body_part": "Arms",
            "modality": "DUMBBELL",
        }

        response = await client.post("/api/v1/exercises/", json=exercise_data)

        # Without auth, this should return 401/403
        assert response.status_code in [401, 403]

    async def test_update_exercise_success(
        self,
        authenticated_client: AsyncClient,
        user_exercise: Exercise,
        sample_user: User,
    ):
        """Test successful exercise update."""
        # Extract IDs early to avoid lazy loading issues
        exercise_id = user_exercise.id
        user_id = sample_user.id

        update_data = {"name": "Updated Exercise Name", "body_part": "Shoulders"}

        response = await authenticated_client.patch(
            f"/api/v1/exercises/{exercise_id}", json=update_data
        )

        assert response.status_code == 200
        data = response.json()

        assert data["id"] == exercise_id
        assert data["name"] == "Updated Exercise Name"
        assert data["body_part"] == "Shoulders"
        assert data["updated_by_user_id"] == user_id

    async def test_update_exercise_not_owned(
        self, another_authenticated_client: AsyncClient, user_exercise: Exercise
    ):
        """Test updating exercise not owned by current user."""
        # Extract ID early to avoid lazy loading issues
        exercise_id = user_exercise.id

        update_data = {"name": "Trying to Update"}

        response = await another_authenticated_client.patch(
            f"/api/v1/exercises/{exercise_id}", json=update_data
        )

        # Should get 400 because users can only modify their own exercises (ValidationError)
        assert response.status_code == 400
        data = response.json()
        assert "only modify your own exercises" in data["detail"]

    async def test_delete_exercise_success(
        self, authenticated_client: AsyncClient, user_exercise: Exercise
    ):
        """Test successful exercise deletion."""
        # Extract ID early to avoid lazy loading issues
        exercise_id = user_exercise.id

        response = await authenticated_client.delete(f"/api/v1/exercises/{exercise_id}")

        assert response.status_code == 204

    async def test_delete_exercise_not_owned(
        self, another_authenticated_client: AsyncClient, user_exercise: Exercise
    ):
        """Test deleting exercise not owned by current user."""
        # Extract ID early to avoid lazy loading issues
        exercise_id = user_exercise.id

        response = await another_authenticated_client.delete(
            f"/api/v1/exercises/{exercise_id}"
        )

        # Should get 400 because users can only delete their own exercises (ValidationError)
        assert response.status_code == 400
        data = response.json()
        assert "only delete your own exercises" in data["detail"]

    async def test_get_my_exercises_success(
        self,
        authenticated_client: AsyncClient,
        user_exercise: Exercise,
        sample_user: User,
    ):
        """Test getting user's own exercises."""
        # Extract IDs early to avoid lazy loading issues
        user_id = sample_user.id
        exercise_id = user_exercise.id

        response = await authenticated_client.get("/api/v1/exercises/my-exercises")

        assert response.status_code == 200
        data = response.json()

        assert "items" in data
        assert len(data["items"]) >= 1

        # Find our exercise in the results
        exercise_found = False
        for item in data["items"]:
            if item["id"] == exercise_id:
                exercise_found = True
                assert item["created_by_user_id"] == user_id
                assert item["is_user_created"] is True
                break

        assert exercise_found, "User's exercise should be in the results"

    async def test_get_body_parts(self, client: AsyncClient, multiple_exercises):  # noqa: ARG002
        """Test getting available body parts."""
        response = await client.get("/api/v1/exercises/body-parts")

        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)
        assert len(data) >= 3  # At least Chest, Legs, Back
        assert "Chest" in data
        assert "Legs" in data

    async def test_get_modalities(self, client: AsyncClient):
        """Test getting available exercise modalities."""
        response = await client.get("/api/v1/exercises/modalities")

        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)
        expected_modalities = [e.value for e in ExerciseModality]

        for modality in expected_modalities:
            assert modality in data

    async def test_get_user_exercises_without_auth(self, client: AsyncClient):
        """Test getting user exercises without authentication."""
        response = await client.get("/api/v1/exercises/my-exercises")

        assert response.status_code in [401, 403]

    async def test_get_system_exercises(self, client: AsyncClient, multiple_exercises):  # noqa: ARG002
        """Test getting system exercises."""
        response = await client.get("/api/v1/exercises/system")

        assert response.status_code == 200
        data = response.json()

        assert "items" in data
        assert data["total"] >= 3  # At least 3 system exercises

        for item in data["items"]:
            assert item["is_user_created"] is False

    async def test_get_exercises_by_body_part(
        self,
        client: AsyncClient,
        multiple_exercises,  # noqa: ARG002
    ):
        """Test getting exercises filtered by body part via endpoint."""
        response = await client.get("/api/v1/exercises/by-body-part/Chest")

        assert response.status_code == 200
        data = response.json()

        assert "items" in data
        for item in data["items"]:
            assert "Chest" in item["body_part"]

    async def test_get_exercises_by_modality(
        self,
        client: AsyncClient,
        multiple_exercises,  # noqa: ARG002
    ):
        """Test getting exercises filtered by modality via endpoint."""
        response = await client.get("/api/v1/exercises/by-modality/BARBELL")

        assert response.status_code == 200
        data = response.json()

        assert "items" in data
        for item in data["items"]:
            assert item["modality"] == "BARBELL"

    async def test_get_exercises_by_invalid_modality(self, client: AsyncClient):
        """Test getting exercises with invalid modality."""
        response = await client.get("/api/v1/exercises/by-modality/INVALID")

        assert response.status_code == 422  # Validation error

    async def test_response_format_consistency(
        self, client: AsyncClient, system_exercise
    ):
        """Test that API responses have consistent format."""
        # Extract ID early
        exercise_id = system_exercise.id

        # Test single exercise response
        response = await client.get(f"/api/v1/exercises/{exercise_id}")
        assert response.status_code == 200
        exercise_data = response.json()

        required_fields = [
            "id",
            "name",
            "body_part",
            "modality",
            "picture_url",
            "is_user_created",
            "created_by_user_id",
            "updated_by_user_id",
            "created_at",
            "updated_at",
        ]

        for field in required_fields:
            assert field in exercise_data

        # Test paginated response
        response = await client.get("/api/v1/exercises/")
        assert response.status_code == 200
        paginated_data = response.json()

        paginated_fields = ["items", "total", "page", "size", "pages"]
        for field in paginated_fields:
            assert field in paginated_data

        # Items should have the same format
        if paginated_data["items"]:
            item = paginated_data["items"][0]
            for field in required_fields:
                assert field in item

    async def test_error_handling_invalid_json(self, client: AsyncClient):
        """Test error handling for invalid JSON."""
        response = await client.post(
            "/api/v1/exercises/",
            content="invalid json",
            headers={"content-type": "application/json"},
        )

        assert response.status_code == 422

    async def test_update_exercise_without_auth(
        self, client: AsyncClient, user_exercise: Exercise
    ):
        """Test updating exercise without authentication."""
        # Extract ID early
        exercise_id = user_exercise.id

        update_data = {"name": "Updated Name"}

        response = await client.patch(
            f"/api/v1/exercises/{exercise_id}", json=update_data
        )

        assert response.status_code in [401, 403]

    async def test_update_exercise_nonexistent(self, authenticated_client: AsyncClient):
        """Test updating non-existent exercise."""
        update_data = {"name": "Updated Name"}

        response = await authenticated_client.patch(
            "/api/v1/exercises/999999", json=update_data
        )

        assert response.status_code == 404

    async def test_delete_exercise_without_auth(
        self, client: AsyncClient, user_exercise: Exercise
    ):
        """Test deleting exercise without authentication."""
        # Extract ID early
        exercise_id = user_exercise.id

        response = await client.delete(f"/api/v1/exercises/{exercise_id}")

        assert response.status_code in [401, 403]

    async def test_delete_exercise_nonexistent(self, authenticated_client: AsyncClient):
        """Test deleting non-existent exercise."""
        response = await authenticated_client.delete("/api/v1/exercises/999999")

        assert response.status_code == 404
