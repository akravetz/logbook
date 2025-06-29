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


@pytest.fixture
async def sample_user(session: AsyncSession) -> User:
    """Create a sample user for testing."""
    user = User(
        email_address="testuser@example.com",
        google_id="test_google_id_123",
        name="Test User",
        is_active=True,
        is_admin=False,
    )
    session.add(user)
    await session.flush()
    await session.refresh(user)
    return user


@pytest.fixture
async def another_user(session: AsyncSession) -> User:
    """Create another user for permission testing."""
    user = User(
        email_address="anotheruser@example.com",
        google_id="another_google_id_456",
        name="Another User",
        is_active=True,
        is_admin=False,
    )
    session.add(user)
    await session.flush()
    await session.refresh(user)
    return user


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
async def user_exercise(session: AsyncSession, sample_user: User) -> Exercise:
    """Create a user exercise for testing."""
    exercise = Exercise(
        name="Custom Push Up",
        body_part="Chest",
        modality=ExerciseModality.BODYWEIGHT,
        picture_url="https://example.com/pushup.jpg",
        is_user_created=True,
        created_by_user_id=sample_user.id,
        updated_by_user_id=sample_user.id,
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
    session: AsyncSession, sample_user: User, another_user: User
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
            created_by_user_id=sample_user.id,
            updated_by_user_id=sample_user.id,
        ),
        Exercise(
            name="User Leg Press",
            body_part="Legs",
            modality=ExerciseModality.MACHINE,
            is_user_created=True,
            created_by_user_id=sample_user.id,
            updated_by_user_id=sample_user.id,
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
    return Pagination(page=1, size=20)


@pytest.fixture
async def authenticated_client(client, sample_user: User):
    """Create an authenticated client by overriding the auth dependency."""
    from workout_api.auth.dependencies import get_current_user_from_token
    from workout_api.core.main import app

    async def override_get_current_user():
        return sample_user

    app.dependency_overrides[get_current_user_from_token] = override_get_current_user

    yield client

    # Clean up
    if get_current_user_from_token in app.dependency_overrides:
        del app.dependency_overrides[get_current_user_from_token]


@pytest.fixture
async def another_authenticated_client(client, another_user: User):
    """Create an authenticated client for another user."""
    from workout_api.auth.dependencies import get_current_user_from_token
    from workout_api.core.main import app

    async def override_get_current_user():
        return another_user

    app.dependency_overrides[get_current_user_from_token] = override_get_current_user

    yield client

    # Clean up
    if get_current_user_from_token in app.dependency_overrides:
        del app.dependency_overrides[get_current_user_from_token]
