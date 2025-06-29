"""Exercise test fixtures."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from workout_api.exercises.models import Exercise, ExerciseModality
from workout_api.exercises.repository import ExerciseRepository
from workout_api.exercises.schemas import ExerciseCreate, ExerciseFilters, Pagination
from workout_api.exercises.service import ExerciseService
from workout_api.users.models import User


@pytest.fixture
async def exercise_repository(session: AsyncSession) -> ExerciseRepository:
    """Get exercise repository for testing."""
    return ExerciseRepository(session)


@pytest.fixture
async def exercise_service(session: AsyncSession) -> ExerciseService:
    """Get exercise service for testing."""
    return ExerciseService(session)


# Note: User fixtures (test_user, another_user, etc.) are now provided by main conftest.py


@pytest.fixture
async def system_exercise(session: AsyncSession) -> Exercise:
    """Create a system exercise for testing."""
    exercise = Exercise(
        name="Barbell Bench Press",
        body_part="Chest",
        modality=ExerciseModality.BARBELL,
        picture_url="https://example.com/bench-press.jpg",
        is_user_created=False,
        created_by_user_id=None,
        updated_by_user_id=None,
    )
    session.add(exercise)
    await session.flush()
    await session.refresh(exercise)
    return exercise


@pytest.fixture
async def user_exercise(session: AsyncSession, test_user: User) -> Exercise:
    """Create a user exercise for testing."""
    exercise = Exercise(
        name="Custom Push Up",
        body_part="Chest",
        modality=ExerciseModality.BODYWEIGHT,
        picture_url="https://example.com/pushup.jpg",
        is_user_created=True,
        created_by_user_id=test_user.id,
        updated_by_user_id=test_user.id,
    )
    session.add(exercise)
    await session.flush()
    await session.refresh(exercise)
    return exercise


@pytest.fixture
async def another_user_exercise(session: AsyncSession, another_user: User) -> Exercise:
    """Create an exercise for another user (for permission testing)."""
    exercise = Exercise(
        name="Private Exercise",
        body_part="Legs",
        modality=ExerciseModality.DUMBBELL,
        picture_url="https://example.com/private.jpg",
        is_user_created=True,
        created_by_user_id=another_user.id,
        updated_by_user_id=another_user.id,
    )
    session.add(exercise)
    await session.flush()
    await session.refresh(exercise)
    return exercise


@pytest.fixture
async def multiple_exercises(
    session: AsyncSession, test_user: User, another_user: User
) -> list[Exercise]:
    """Create multiple exercises for testing."""
    exercises = [
        # System exercises
        Exercise(
            name="Squat",
            body_part="Legs",
            modality=ExerciseModality.BARBELL,
            is_user_created=False,
        ),
        Exercise(
            name="Deadlift",
            body_part="Back",
            modality=ExerciseModality.BARBELL,
            is_user_created=False,
        ),
        Exercise(
            name="Pull Up",
            body_part="Back",
            modality=ExerciseModality.BODYWEIGHT,
            is_user_created=False,
        ),
        Exercise(
            name="Bench Press",
            body_part="Chest",
            modality=ExerciseModality.BARBELL,
            is_user_created=False,
        ),
        # User exercises
        Exercise(
            name="User Chest Fly",
            body_part="Chest",
            modality=ExerciseModality.DUMBBELL,
            is_user_created=True,
            created_by_user_id=test_user.id,
            updated_by_user_id=test_user.id,
        ),
        Exercise(
            name="User Leg Press",
            body_part="Legs",
            modality=ExerciseModality.MACHINE,
            is_user_created=True,
            created_by_user_id=test_user.id,
            updated_by_user_id=test_user.id,
        ),
        # Another user's exercises
        Exercise(
            name="Another User Exercise",
            body_part="Arms",
            modality=ExerciseModality.CABLE,
            is_user_created=True,
            created_by_user_id=another_user.id,
            updated_by_user_id=another_user.id,
        ),
    ]

    for exercise in exercises:
        session.add(exercise)

    await session.flush()
    for exercise in exercises:
        await session.refresh(exercise)

    return exercises


@pytest.fixture
def sample_exercise_create() -> ExerciseCreate:
    """Sample exercise create data."""
    return ExerciseCreate(
        name="Test Exercise",
        body_part="Chest",
        modality=ExerciseModality.DUMBBELL,
        picture_url="https://example.com/test.jpg",
    )


@pytest.fixture
def sample_filters() -> ExerciseFilters:
    """Sample exercise filters."""
    return ExerciseFilters(
        name="Test",
        body_part="Chest",
        modality=ExerciseModality.DUMBBELL,
        is_user_created=True,
    )


@pytest.fixture
def sample_pagination() -> Pagination:
    """Sample pagination parameters."""
    return Pagination(page=1, per_page=10)
