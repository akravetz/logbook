"""Test exercise service."""

import pytest

from workout_api.exercises.models import ExerciseModality
from workout_api.exercises.schemas import (
    ExerciseCreate,
    ExerciseFilters,
    ExerciseResponse,
    ExerciseUpdate,
    Pagination,
)
from workout_api.exercises.service import ExerciseService
from workout_api.shared.exceptions import NotFoundError, ValidationError
from workout_api.users.models import User


class TestExerciseService:
    """Test exercise service operations."""

    async def test_get_by_id_existing(
        self,
        exercise_service: ExerciseService,
        system_exercise,  # noqa: ARG002
    ):
        """Test getting exercise by existing ID returns Pydantic model."""
        # Extract ID early
        exercise_id = system_exercise.id

        result = await exercise_service.get_by_id(exercise_id)

        assert result is not None
        assert isinstance(result, ExerciseResponse)
        assert result.id == exercise_id
        assert result.name == "Barbell Bench Press"

    async def test_get_by_id_nonexistent(self, exercise_service: ExerciseService):
        """Test getting exercise by non-existent ID raises NotFoundError."""
        with pytest.raises(NotFoundError, match="Exercise not found with ID: 999999"):
            await exercise_service.get_by_id(999999)

    async def test_get_by_name_existing(
        self,
        exercise_service: ExerciseService,
        system_exercise,  # noqa: ARG002
        test_user: User,
    ):
        """Test getting exercise by existing name."""
        # Extract user ID early
        user_id = test_user.id

        result = await exercise_service.get_by_name("Barbell Bench Press", user_id)

        assert result is not None
        assert isinstance(result, ExerciseResponse)
        assert result.name == "Barbell Bench Press"

    async def test_get_by_name_nonexistent(
        self, exercise_service: ExerciseService, test_user: User
    ):
        """Test getting exercise by non-existent name returns None."""
        # Extract user ID early
        user_id = test_user.id

        result = await exercise_service.get_by_name("Non Existent Exercise", user_id)
        assert result is None

    async def test_search_returns_pydantic_models(
        self,
        exercise_service: ExerciseService,
        multiple_exercises,  # noqa: ARG002
    ):
        """Test search returns Page of Pydantic models."""
        filters = ExerciseFilters()
        pagination = Pagination(page=1, size=10)

        result = await exercise_service.search(filters, pagination)

        assert result.total >= len(multiple_exercises)
        assert len(result.items) >= len(multiple_exercises)
        for item in result.items:
            assert isinstance(item, ExerciseResponse)

    async def test_search_with_name_filter(
        self,
        exercise_service: ExerciseService,
        multiple_exercises,  # noqa: ARG002
    ):
        """Test search with name filter."""
        filters = ExerciseFilters(name="User")
        pagination = Pagination(page=1, size=10)

        result = await exercise_service.search(filters, pagination)

        assert result.total >= 2
        for item in result.items:
            assert "User" in item.name

    async def test_search_with_user_permissions(
        self,
        exercise_service: ExerciseService,
        test_user: User,
        multiple_exercises,  # noqa: ARG002
    ):
        """Test search respects user permissions."""
        # Extract user ID early
        user_id = test_user.id

        filters = ExerciseFilters()
        pagination = Pagination(page=1, size=100)

        result = await exercise_service.search(filters, pagination, user_id)

        # Should include user's exercises and system exercises, but not other users'
        user_exercises = [
            e
            for e in result.items
            if e.is_user_created and e.created_by_user_id == user_id
        ]
        system_exercises = [e for e in result.items if not e.is_user_created]
        other_user_exercises = [
            e
            for e in result.items
            if e.is_user_created and e.created_by_user_id != user_id
        ]

        assert len(user_exercises) >= 2
        assert len(system_exercises) >= 3
        assert len(other_user_exercises) == 0

    async def test_create_user_exercise(
        self, exercise_service: ExerciseService, test_user: User
    ):
        """Test creating user exercise."""
        # Extract user ID early
        user_id = test_user.id

        exercise_data = ExerciseCreate(
            name="New Service Test Exercise",
            body_part="Arms",
            modality=ExerciseModality.CABLE,
            picture_url="https://example.com/new.jpg",
        )

        result = await exercise_service.create(exercise_data, user_id)

        assert isinstance(result, ExerciseResponse)
        assert result.name == "New Service Test Exercise"
        assert result.body_part == "Arms"
        assert result.modality == ExerciseModality.CABLE
        assert result.is_user_created is True
        assert result.created_by_user_id == user_id

    async def test_create_duplicate_name_validation(
        self,
        exercise_service: ExerciseService,
        test_user: User,
        system_exercise,  # noqa: ARG002
    ):
        """Test creating exercise with duplicate name raises ValidationError."""
        # Extract user ID early
        user_id = test_user.id

        exercise_data = ExerciseCreate(
            name="Barbell Bench Press",  # Duplicate name
            body_part="Chest",
            modality=ExerciseModality.BARBELL,
        )

        with pytest.raises(
            ValidationError,
            match="Exercise with name 'Barbell Bench Press' already exists",
        ):
            await exercise_service.create(exercise_data, user_id)

    async def test_update_existing_exercise(
        self, exercise_service: ExerciseService, test_user: User, user_exercise
    ):
        """Test updating existing exercise."""
        # Extract IDs and values early
        exercise_id = user_exercise.id
        user_id = test_user.id
        original_modality = user_exercise.modality

        update_data = ExerciseUpdate(
            name="Updated Service Exercise", body_part="Updated Body Part"
        )

        result = await exercise_service.update(exercise_id, update_data, user_id)

        assert isinstance(result, ExerciseResponse)
        assert result.name == "Updated Service Exercise"
        assert result.body_part == "Updated Body Part"
        assert result.modality == original_modality  # Unchanged

    async def test_update_nonexistent_exercise(
        self, exercise_service: ExerciseService, test_user: User
    ):
        """Test updating non-existent exercise raises NotFoundError."""
        # Extract user ID early
        user_id = test_user.id

        update_data = ExerciseUpdate(name="Updated Name")

        with pytest.raises(NotFoundError, match="Exercise not found with ID: 999999"):
            await exercise_service.update(999999, update_data, user_id)

    async def test_update_permission_denied(
        self,
        exercise_service: ExerciseService,
        test_user: User,
        system_exercise,  # noqa: ARG002
    ):
        """Test updating exercise without permission raises ValidationError."""
        # Extract IDs early
        exercise_id = system_exercise.id
        user_id = test_user.id

        update_data = ExerciseUpdate(name="Hacked Name")

        with pytest.raises(
            ValidationError, match="You can only modify your own exercises"
        ):
            await exercise_service.update(exercise_id, update_data, user_id)

    async def test_delete_existing_exercise(
        self, exercise_service: ExerciseService, test_user: User, user_exercise
    ):
        """Test deleting existing exercise."""
        # Extract IDs early
        exercise_id = user_exercise.id
        user_id = test_user.id

        result = await exercise_service.delete(exercise_id, user_id)
        assert result is True

    async def test_delete_nonexistent_exercise(
        self, exercise_service: ExerciseService, test_user: User
    ):
        """Test deleting non-existent exercise raises NotFoundError."""
        # Extract user ID early
        user_id = test_user.id

        with pytest.raises(NotFoundError, match="Exercise not found with ID: 999999"):
            await exercise_service.delete(999999, user_id)

    async def test_delete_permission_denied(
        self,
        exercise_service: ExerciseService,
        test_user: User,
        system_exercise,  # noqa: ARG002
    ):
        """Test deleting exercise without permission raises ValidationError."""
        # Extract IDs early
        exercise_id = system_exercise.id
        user_id = test_user.id

        with pytest.raises(
            ValidationError, match="You can only delete your own exercises"
        ):
            await exercise_service.delete(exercise_id, user_id)

    async def test_get_user_exercises(
        self,
        exercise_service: ExerciseService,
        test_user: User,
        multiple_exercises,  # noqa: ARG002
    ):
        """Test getting user's own exercises."""
        # Extract user ID early
        user_id = test_user.id

        pagination = Pagination(page=1, size=10)
        result = await exercise_service.get_user_exercises(user_id, pagination)

        assert result.total >= 2
        for item in result.items:
            assert isinstance(item, ExerciseResponse)
            assert item.is_user_created is True
            assert item.created_by_user_id == user_id

    async def test_get_system_exercises(
        self,
        exercise_service: ExerciseService,
        multiple_exercises,  # noqa: ARG002
    ):
        """Test getting system exercises."""
        pagination = Pagination(page=1, size=10)
        result = await exercise_service.get_system_exercises(pagination)

        assert result.total >= 3
        for item in result.items:
            assert isinstance(item, ExerciseResponse)
            assert item.is_user_created is False
