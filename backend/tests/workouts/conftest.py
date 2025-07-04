"""Workout test fixtures and configuration."""

from datetime import UTC, datetime

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from workout_api.exercises.models import Exercise, ExerciseModality
from workout_api.users.models import User
from workout_api.workouts.models import ExerciseExecution, Set, Workout
from workout_api.workouts.repository import WorkoutRepository
from workout_api.workouts.service import WorkoutService

# Note: User fixtures (test_user, another_user, etc.) are now provided by main conftest.py


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
async def sample_workout(session: AsyncSession, test_user: User) -> Workout:
    """Create a sample workout for testing."""
    user_id = test_user.id

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
async def finished_workout(session: AsyncSession, test_user: User) -> Workout:
    """Create a finished workout for testing."""
    user_id = test_user.id

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
    workout = sample_workout
    # Extract workout id early
    workout_id = workout.id
    sample_exercise_id = sample_exercise.id
    another_exercise_id = another_exercise.id

    # Create exercise executions
    execution1 = ExerciseExecution(
        workout_id=workout_id,
        exercise_id=sample_exercise_id,
        exercise_order=1,
    )
    execution2 = ExerciseExecution(
        workout_id=workout_id,
        exercise_id=another_exercise_id,
        exercise_order=2,
    )

    session.add(execution1)
    session.add(execution2)
    await session.flush()
    await session.refresh(execution1)
    await session.refresh(execution2)

    # Create sets for first exercise
    sets1 = [
        Set(
            workout_id=workout_id,
            exercise_id=sample_exercise_id,
            weight=100,
            clean_reps=10,
            forced_reps=0,
        ),
        Set(
            workout_id=workout_id,
            exercise_id=sample_exercise_id,
            weight=100,
            clean_reps=8,
            forced_reps=2,
        ),
    ]

    # Create sets for second exercise
    sets2 = [
        Set(
            workout_id=workout_id,
            exercise_id=another_exercise_id,
            weight=80,
            clean_reps=12,
            forced_reps=0,
        ),
    ]

    for set_obj in sets1 + sets2:
        session.add(set_obj)

    await session.flush()
    for set_obj in sets1 + sets2:
        await session.refresh(set_obj)

    # Extract set attributes early
    for set_obj in sets1 + sets2:
        _ = (
            set_obj.id,
            set_obj.workout_id,
            set_obj.exercise_id,
            set_obj.weight,
            set_obj.clean_reps,
            set_obj.forced_reps,
            set_obj.note_text,
            set_obj.created_at,
            set_obj.updated_at,
        )

    return workout


@pytest.fixture
def workout_repository(session: AsyncSession) -> WorkoutRepository:
    """Get workout repository for testing."""
    return WorkoutRepository(session)


@pytest.fixture
def workout_service(
    session: AsyncSession, workout_repository: WorkoutRepository
) -> WorkoutService:
    """Get workout service for testing."""
    return WorkoutService(workout_repository, session)
