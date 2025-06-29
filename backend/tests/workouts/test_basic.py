"""Basic workout tests to verify infrastructure."""

import pytest

from workout_api.users.models import User
from workout_api.workouts.models import Workout
from workout_api.workouts.repository import WorkoutRepository
from workout_api.workouts.service import WorkoutService

pytestmark = pytest.mark.anyio


class TestWorkoutBasic:
    """Basic workout tests."""

    async def test_repository_creation(self, workout_repository: WorkoutRepository):
        """Test that workout repository can be created."""
        assert workout_repository is not None

    async def test_service_creation(self, workout_service: WorkoutService):
        """Test that workout service can be created."""
        assert workout_service is not None

    async def test_sample_workout_fixture(
        self, sample_workout: Workout, test_user: User
    ):
        """Test that sample workout fixture works."""
        assert sample_workout.id is not None
        assert sample_workout.created_by_user_id == test_user.id
        assert sample_workout.finished_at is None

    async def test_create_workout(
        self, workout_repository: WorkoutRepository, test_user: User
    ):
        """Test creating a workout through repository."""
        user_id = test_user.id

        workout = await workout_repository.create(user_id)

        assert workout.id is not None
        assert workout.created_by_user_id == user_id
        assert workout.finished_at is None
