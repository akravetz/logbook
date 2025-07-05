# Backend Testing Guide

This document provides comprehensive guidance for writing, running, and maintaining tests in the LogBK backend application.

## Overview

The backend testing strategy follows a **multi-layer approach** with strong emphasis on **transaction isolation**, **real database testing**, and **comprehensive coverage** across the application stack.

### Test Types

- **Unit Tests**: Repository and Service layer testing with isolated components
- **Integration Tests**: Router/API endpoint testing with full HTTP stack
- **End-to-end Tests**: Complete request/response flows with authentication
- **Infrastructure Tests**: Database transaction isolation and core functionality

## Architecture & Infrastructure

### Database Testing Strategy

#### TestContainers Integration
- **Real PostgreSQL instances** for authentic testing environment
- **Session-scoped containers** for performance optimization
- **Automatic cleanup** with proper container lifecycle management

```python
@pytest.fixture(scope="session")
def postgres_container():
    """Start PostgreSQL container for entire test session."""
    with PostgresContainer("postgres:16", driver="asyncpg") as postgres:
        yield postgres
```

#### Transaction Isolation Pattern
- **Guaranteed clean state** between tests via transaction rollback
- **Savepoint-based sessions** for proper isolation
- **No test pollution** - each test starts with clean database

```python
@pytest.fixture
async def session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create test session with transaction isolation."""
    async with test_engine.connect() as connection:
        trans = await connection.begin()
        session = AsyncSession(
            bind=connection, join_transaction_mode="create_savepoint"
        )
        try:
            yield session
        finally:
            await session.close()
            await trans.rollback()  # Rollback ensures isolation
```

### Async/Await Support

#### Complete Async Stack
- **Full anyio integration** with pytest
- **Async session management** with proper cleanup
- **Lazy loading prevention** to avoid `MissingGreenlet` errors

```python
pytestmark = pytest.mark.anyio  # Mark all tests as async

# Extract attributes early to prevent lazy loading issues
async def _create_user_from_data(session: AsyncSession, user_data: dict[str, Any]) -> User:
    user = User(**user_data)
    session.add(user)
    await session.flush()
    await session.refresh(user)

    # Extract all attributes early to prevent MissingGreenlet errors
    _ = (user.id, user.email_address, user.google_id, user.name,
         user.profile_image_url, user.is_active, user.is_admin,
         user.created_at, user.updated_at)
    return user
```

## Directory Structure & Organization

### Domain-Driven Test Organization

```
backend/tests/
├── conftest.py              # Global fixtures and configuration
├── auth/                    # Authentication domain tests
│   ├── conftest.py         # Auth-specific fixtures
│   ├── test_auth_router.py # API endpoint tests
│   ├── test_auth_service.py # Business logic tests
│   └── test_jwt.py         # Component tests
├── exercises/              # Exercise domain tests
│   ├── conftest.py         # Exercise fixtures
│   ├── test_exercise_repository.py
│   ├── test_exercise_service.py
│   └── test_exercise_router.py
├── users/                  # User domain tests
├── workouts/              # Workout domain tests
└── voice/                 # Voice transcription tests
```

### Test Layer Patterns

#### Repository Layer Tests (`test_*_repository.py`)
- **Data access testing** with real database operations
- **Query verification** and constraint testing
- **Relationship handling** and foreign key constraints

#### Service Layer Tests (`test_*_service.py`)
- **Business logic validation** with mocked dependencies
- **Permission and authorization** testing
- **Complex workflow** testing

#### Router Layer Tests (`test_*_router.py`)
- **Full HTTP endpoint testing** with real requests/responses
- **Authentication and authorization** integration
- **Input validation** and error handling
- **Complete request/response cycles**

## Fixture Patterns & Best Practices

### Global Fixtures (`conftest.py`)

#### Core Infrastructure
```python
@pytest.fixture(scope="session")
async def test_engine(postgres_container, anyio_backend):
    """Create test database engine with session scope."""
    database_url = postgres_container.get_connection_url()
    engine = create_async_engine(database_url, echo=False)

    # Create all tables once per session
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Cleanup
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
    finally:
        await engine.dispose()
```

#### User Management
```python
@pytest.fixture
def test_user_data() -> dict[str, Any]:
    """Standard test user data - shared across modules."""
    return {
        "id": 1,
        "email_address": "test@example.com",
        "google_id": "google_user_123",
        "name": "Test User",
        "profile_image_url": "https://example.com/avatar.jpg",
        "is_active": True,
        "is_admin": False,
    }

@pytest.fixture
async def test_user(session: AsyncSession, test_user_data: dict[str, Any]) -> User:
    """Create standard test user in database."""
    return await _create_user_from_data(session, test_user_data)
```

### Domain-Specific Fixtures

#### Exercise Domain (`exercises/conftest.py`)
```python
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
async def multiple_exercises(session: AsyncSession, test_user: User, another_user: User) -> list[Exercise]:
    """Create multiple exercises for testing various scenarios."""
    # Create system exercises, user exercises, and another user's exercises
    # for comprehensive permission and visibility testing
```

### Authentication Testing

#### HTTP Client Authentication
```python
@pytest.fixture
async def authenticated_client(
    client: AsyncClient, test_user: User, session: AsyncSession
) -> AsyncClient:
    """Create authenticated HTTP client for standard user."""
    user_id = test_user.id

    async def override_get_current_user_from_token():
        # Get fresh user object to avoid detached instance issues
        stmt = select(User).where(User.id == user_id)
        result = await session.execute(stmt)
        fresh_user = result.scalar_one()
        return fresh_user

    app.dependency_overrides[get_current_user_from_token] = override_get_current_user_from_token
    yield client

    # Clean up override
    if get_current_user_from_token in app.dependency_overrides:
        del app.dependency_overrides[get_current_user_from_token]
```

## Testing Patterns & Conventions

### Test Class Organization

```python
class TestExerciseService:
    """Test exercise service operations."""

    async def test_get_by_id_existing(
        self, exercise_service: ExerciseService, system_exercise
    ):
        """Test getting exercise by existing ID returns Pydantic model."""
        exercise_id = system_exercise.id  # Extract ID early

        result = await exercise_service.get_by_id(exercise_id)

        assert result is not None
        assert isinstance(result, ExerciseResponse)
        assert result.id == exercise_id
        assert result.name == "Barbell Bench Press"

    async def test_get_by_id_nonexistent(self, exercise_service: ExerciseService):
        """Test getting exercise by non-existent ID raises NotFoundError."""
        with pytest.raises(NotFoundError, match="Exercise not found with ID: 999999"):
            await exercise_service.get_by_id(999999)
```

### Naming Conventions

#### Test Methods
- `test_<operation>_<scenario>` - e.g., `test_create_user_success`
- `test_<operation>_<error_case>` - e.g., `test_get_by_id_nonexistent`
- `test_<operation>_<permission_case>` - e.g., `test_update_permission_denied`

#### Test Files
- `test_<module>_<layer>.py` - e.g., `test_exercise_service.py`
- `conftest.py` - Domain-specific fixtures

#### Fixture Naming
- **Data fixtures**: `test_user_data`, `sample_exercise_create`
- **Model fixtures**: `test_user`, `system_exercise`, `sample_workout`
- **Service fixtures**: `exercise_service`, `workout_repository`
- **Client fixtures**: `authenticated_client`, `admin_authenticated_client`

### Error Testing Patterns

#### Exception Testing
```python
async def test_create_duplicate_name_validation(
    self, exercise_service: ExerciseService, test_user: User, system_exercise
):
    """Test creating exercise with duplicate name raises ValidationError."""
    user_id = test_user.id

    exercise_data = ExerciseCreate(
        name="Barbell Bench Press",  # Duplicate name
        body_part="Chest",
        modality=ExerciseModality.BARBELL,
    )

    with pytest.raises(
        ValidationError,
        match="Exercise with name 'Barbell Bench Press' already exists"
    ):
        await exercise_service.create(exercise_data, user_id)
```

#### HTTP Error Testing
```python
async def test_create_workout_without_auth(self, client: AsyncClient):
    """Test creating workout without authentication returns 403."""
    response = await client.post("/api/v1/workouts/")

    assert response.status_code == 403
```

### Permission Testing Patterns

```python
async def test_update_permission_denied(
    self, exercise_service: ExerciseService, test_user: User, system_exercise
):
    """Test updating exercise without permission raises ValidationError."""
    exercise_id = system_exercise.id
    user_id = test_user.id

    update_data = ExerciseUpdate(name="Hacked Name")

    with pytest.raises(
        ValidationError, match="You can only modify your own exercises"
    ):
        await exercise_service.update(exercise_id, update_data, user_id)
```

## Mocking Strategies

### External Service Mocking

#### Google OAuth Mocking
```python
@pytest.fixture
def mock_google_verifier():
    """Create mock Google token verifier."""
    mock = Mock(spec=GoogleTokenVerifier)
    mock.verify_access_token = AsyncMock()
    return mock

@pytest.fixture
def sample_google_token_info():
    """Create sample Google token info."""
    return GoogleTokenInfo(
        email="test@example.com",
        name="Test User",
        picture="https://example.com/avatar.jpg",
        user_id="google_123",
        email_verified=True,
        audience="test_client_id",
        expires_in=3600,
    )
```

### Dependency Injection for Testing

```python
@pytest.fixture
async def client(session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create async test client with database dependency override."""

    async def override_get_session():
        yield session

    app.dependency_overrides[get_session] = override_get_session

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            yield ac
    finally:
        app.dependency_overrides.clear()
```

## Running Tests

### Basic Commands

```bash
# Run all tests
task test

# Run tests with coverage
task test-cov

# Run specific test file
task test -- tests/exercises/test_exercise_service.py

# Run specific test method
task test -- tests/exercises/test_exercise_service.py::TestExerciseService::test_get_by_id_existing

# Run tests with verbose output
task test -- -v

# Run tests with specific markers
task test -- -m "not slow"
```

### Coverage Reporting

```bash
# Generate HTML coverage report
task test-cov

# Open coverage report
open htmlcov/index.html
```

## Best Practices & Guidelines

### Database Testing
1. **Always use real PostgreSQL** via TestContainers for authentic testing
2. **Extract model attributes early** to prevent lazy loading issues
3. **Use transaction isolation** for guaranteed clean state between tests
4. **Flush and refresh** after database operations in fixtures

### Async Testing
1. **Mark all async tests** with `pytest.mark.anyio`
2. **Properly manage async sessions** with dependency injection
3. **Avoid detached instances** by getting fresh objects when needed
4. **Use AsyncMock** for async method mocking

### Fixture Design
1. **Create domain-specific fixtures** in module `conftest.py` files
2. **Use descriptive fixture names** that indicate their purpose
3. **Extract IDs early** to avoid lazy loading in test methods
4. **Share common fixtures** via global `conftest.py`

### Test Organization
1. **Group tests by layer** (repository, service, router)
2. **Use descriptive test method names** that explain the scenario
3. **Test both success and failure cases** comprehensively
4. **Include permission and ownership testing** for all operations

### Performance Considerations
1. **Use session-scoped containers** for database infrastructure
2. **Minimize database setup/teardown** with transaction rollback
3. **Batch fixture creation** when testing multiple scenarios
4. **Consider test execution time** when designing complex fixtures

### Common Pitfalls to Avoid

#### Lazy Loading Issues
```python
# ❌ Wrong - may cause MissingGreenlet error
def test_something(user):
    user_id = user.id  # Accessing lazy-loaded attribute in test

# ✅ Correct - extract early in fixture
@pytest.fixture
async def test_user(session):
    user = User(...)
    session.add(user)
    await session.flush()
    await session.refresh(user)
    # Extract attributes early
    _ = (user.id, user.email_address, ...)
    return user
```

#### Detached Instance Issues
```python
# ❌ Wrong - using stale user object
async def override_get_current_user():
    return test_user  # Detached from session

# ✅ Correct - get fresh object
async def override_get_current_user():
    stmt = select(User).where(User.id == user_id)
    result = await session.execute(stmt)
    return result.scalar_one()
```

#### Authentication Testing
```python
# ❌ Wrong - not cleaning up overrides
app.dependency_overrides[get_current_user] = mock_user

# ✅ Correct - proper cleanup
try:
    app.dependency_overrides[get_current_user] = mock_user
    yield client
finally:
    if get_current_user in app.dependency_overrides:
        del app.dependency_overrides[get_current_user]
```

This testing architecture provides **reliable**, **fast**, and **maintainable** testing with excellent isolation between test cases and realistic database interactions. The patterns described here ensure comprehensive coverage while maintaining good performance and developer experience.
