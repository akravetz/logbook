"""Workout test fixtures and configuration."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from workout_api.exercises.models import Exercise, ExerciseModality
from workout_api.users.models import User
from workout_api.users.repository import UserRepository
from workout_api.workouts.dependencies import (
    get_workout_repository,
    get_workout_service,
)
from workout_api.workouts.models import ExerciseExecution, Set, Workout
from workout_api.workouts.repository import WorkoutRepository
from workout_api.workouts.service import WorkoutService


@pytest.fixture
def user_data():
    """Sample user data for testing."""
    return {
        "email_address": "test@example.com",
        "google_id": "google123",
        "name": "Test User",
        "profile_image_url": "https://example.com/profile.jpg",
        "is_active": True,
        "is_admin": False,
    }


@pytest.fixture
async def sample_user(session: AsyncSession, user_data: dict) -> User:
    """Create a sample user for testing."""
    user_repository = UserRepository(session)
    user = await user_repository.create(user_data)
    # Extract attributes early to prevent lazy loading issues
    _ = (
        user.id,
        user.email_address,
        user.google_id,
        user.name,
        user.profile_image_url,
        user.is_active,
        user.is_admin,
        user.created_at,
        user.updated_at,
    )
    return user


@pytest.fixture
async def another_user(session: AsyncSession) -> User:
    """Create another user for testing permissions."""
    user_repository = UserRepository(session)
    user_data = {
        "email_address": "another@example.com",
        "google_id": "google456",
        "name": "Another User",
        "profile_image_url": "https://example.com/another.jpg",
        "is_active": True,
        "is_admin": False,
    }
    user = await user_repository.create(user_data)
    # Extract attributes early
    _ = (
        user.id,
        user.email_address,
        user.google_id,
        user.name,
        user.profile_image_url,
        user.is_active,
        user.is_admin,
        user.created_at,
        user.updated_at,
    )
    return user


@pytest.fixture
async def sample_exercise(session: AsyncSession) -> Exercise:
    """Create a sample exercise for testing."""
    exercise = Exercise(
        name="Test Exercise",
        body_part="Chest",
        modality=ExerciseModality.DUMBBELL,
        picture_url="https://example.com/test.jpg",
        created_by_user_id=None,  # System exercise
        updated_by_user_id=None,
        is_user_created=False,
    )
    session.add(exercise)
    await session.flush()
    await session.refresh(exercise)
    # Extract attributes early to prevent lazy loading issues
    _ = (
        exercise.id,
        exercise.name,
        exercise.body_part,
        exercise.modality,
        exercise.picture_url,
        exercise.created_by_user_id,
        exercise.updated_by_user_id,
        exercise.is_user_created,
        exercise.created_at,
        exercise.updated_at,
    )
    return exercise


@pytest.fixture
async def another_exercise(session: AsyncSession) -> Exercise:
    """Create another sample exercise for testing."""
    exercise = Exercise(
        name="Another Exercise",
        body_part="Back",
        modality=ExerciseModality.BARBELL,
        picture_url="https://example.com/another.jpg",
        created_by_user_id=None,
        updated_by_user_id=None,
        is_user_created=False,
    )
    session.add(exercise)
    await session.flush()
    await session.refresh(exercise)
    # Extract attributes early
    _ = (
        exercise.id,
        exercise.name,
        exercise.body_part,
        exercise.modality,
        exercise.picture_url,
        exercise.created_by_user_id,
        exercise.updated_by_user_id,
        exercise.is_user_created,
        exercise.created_at,
        exercise.updated_at,
    )
    return exercise


@pytest.fixture
async def sample_workout(session: AsyncSession, sample_user: User) -> Workout:
    """Create a sample workout for testing."""
    user_id = sample_user.id

    workout = Workout(
        created_by_user_id=user_id,
        updated_by_user_id=user_id,
        finished_at=None,
    )
    session.add(workout)
    await session.flush()
    await session.refresh(workout)
    # Extract attributes early to prevent lazy loading issues
    _ = (
        workout.id,
        workout.finished_at,
        workout.created_by_user_id,
        workout.updated_by_user_id,
        workout.created_at,
        workout.updated_at,
    )
    return workout


@pytest.fixture
async def finished_workout(session: AsyncSession, sample_user: User) -> Workout:
    """Create a finished workout for testing."""
    from datetime import UTC, datetime

    user_id = sample_user.id

    workout = Workout(
        created_by_user_id=user_id,
        updated_by_user_id=user_id,
        finished_at=datetime.now(UTC).replace(tzinfo=None),
    )
    session.add(workout)
    await session.flush()
    await session.refresh(workout)
    # Extract attributes early
    _ = (
        workout.id,
        workout.finished_at,
        workout.created_by_user_id,
        workout.updated_by_user_id,
        workout.created_at,
        workout.updated_at,
    )
    return workout


@pytest.fixture
async def workout_with_exercises(
    session: AsyncSession,
    sample_workout: Workout,
    sample_exercise: Exercise,
    another_exercise: Exercise,
) -> Workout:
    """Create a workout with exercise executions and sets."""
    workout_id = sample_workout.id
    exercise1_id = sample_exercise.id
    exercise2_id = another_exercise.id

    # Create first exercise execution
    execution1 = ExerciseExecution(
        workout_id=workout_id,
        exercise_id=exercise1_id,
        exercise_order=1,
        note_text="First exercise notes",
    )
    session.add(execution1)

    # Create second exercise execution
    execution2 = ExerciseExecution(
        workout_id=workout_id,
        exercise_id=exercise2_id,
        exercise_order=2,
        note_text="Second exercise notes",
    )
    session.add(execution2)

    await session.flush()

    # Create sets for first exercise
    set1 = Set(
        workout_id=workout_id,
        exercise_id=exercise1_id,
        note_text="First set",
        weight=20.0,
        clean_reps=12,
        forced_reps=0,
    )
    set2 = Set(
        workout_id=workout_id,
        exercise_id=exercise1_id,
        note_text="Second set",
        weight=20.0,
        clean_reps=10,
        forced_reps=2,
    )

    # Create sets for second exercise
    set3 = Set(
        workout_id=workout_id,
        exercise_id=exercise2_id,
        note_text="Heavy set",
        weight=50.0,
        clean_reps=8,
        forced_reps=0,
    )

    session.add_all([set1, set2, set3])
    await session.flush()

    # Refresh workout to load relationships
    await session.refresh(sample_workout)

    return sample_workout


@pytest.fixture
def workout_repository(session: AsyncSession) -> WorkoutRepository:
    """Get workout repository instance."""
    return get_workout_repository(session)


@pytest.fixture
def workout_service(
    session: AsyncSession, workout_repository: WorkoutRepository
) -> WorkoutService:
    """Get workout service instance."""
    return get_workout_service(workout_repository, session)
