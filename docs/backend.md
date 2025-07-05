# Backend Development Guide

This document provides comprehensive guidance for developing and maintaining the LogBK backend application.

## Architecture Overview

The backend follows a **domain-driven design (DDD)** pattern with clean separation of concerns through a layered architecture:

```
Repository → Service → Router
```

### Core Principles
- **Async-first**: All database operations use async/await with SQLAlchemy async ORM
- **Domain-driven**: Each business domain is self-contained with clear boundaries
- **Type-safe**: Comprehensive type annotations with Pydantic validation
- **Dependency injection**: Comprehensive DI system using FastAPI's dependency system
- **Error handling**: Hierarchical exception system with proper HTTP status mapping

## Directory Structure

```
backend/src/workout_api/
├── core/           # Infrastructure layer
│   ├── config.py      # Application configuration
│   ├── database.py    # Database connection management
│   ├── logging.py     # Logging configuration
│   └── main.py        # FastAPI application entry point
├── shared/         # Common utilities
│   ├── base_model.py  # Base SQLAlchemy model
│   └── exceptions.py  # Custom exception hierarchy
├── seeding/        # Database seeding system
├── auth/           # Authentication domain
├── users/          # User management domain
├── exercises/      # Exercise catalog domain
├── workouts/       # Workout management domain
├── voice/          # Voice transcription domain
└── health/         # Health check endpoints
```

## Domain Structure Pattern

Each domain follows a consistent structure:

```
domain/
├── __init__.py
├── models.py       # SQLAlchemy database models
├── schemas.py      # Pydantic schemas for API requests/responses
├── repository.py   # Data access layer
├── service.py      # Business logic layer
├── router.py       # FastAPI route definitions
└── dependencies.py # Domain-specific dependency injection
```

## Core Infrastructure

### Configuration Management

**Location**: `core/config.py`

```python
class Settings(BaseSettings):
    """Application configuration settings."""

    # Make Settings hashable for use with @lru_cache
    def __hash__(self) -> int:
        # Custom hash implementation for caching

    # Environment settings
    environment: Literal["development", "test", "production"] = "development"

    # Server configuration
    host: str = "0.0.0.0"
    port: int = 8080

    # Database configuration
    database_url: str
    database_pool_size: int = 10

    # Security configuration
    secret_key: str
    jwt_secret_key: str
    session_secret_key: str

    # Derived properties for convenience
    @property
    def database_url_async(self) -> str:
        return str(self.database_url).replace("postgresql://", "postgresql+asyncpg://")

    @property
    def is_development(self) -> bool:
        return self.environment == "development"

@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
```

**Key Features**:
- **Environment-based configuration** with `.env` file support
- **Validation** with Pydantic field validators
- **Caching** with `@lru_cache` for performance
- **Post-initialization** logic for default value handling
- **Type safety** with comprehensive annotations

### Database Management

**Location**: `core/database.py`

```python
class DatabaseManager:
    """Manages database connections and session lifecycle."""

    def __init__(self, settings: Settings):
        self.engine = create_async_engine(
            settings.database_url_async,
            pool_size=settings.database_pool_size,
            max_overflow=settings.database_max_overflow,
            pool_timeout=settings.database_pool_timeout,
        )

    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        async with AsyncSession(self.engine) as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()
```

**Key Features**:
- **Connection pooling** with configurable pool sizes
- **Health monitoring** with connection status tracking
- **Session management** with automatic cleanup
- **Error handling** with automatic rollback

### Logging Configuration

**Location**: `core/logging.py`

```python
def setup_logging() -> None:
    """Set up comprehensive logging configuration."""

    # Different configurations for different environments
    if settings.environment == "production":
        # JSON structured logging for production
        setup_json_logging()
    else:
        # Human-readable logging for development
        setup_console_logging()

    # Configure different loggers
    configure_sqlalchemy_logging()
    configure_hypercorn_logging()
```

**Features**:
- **Environment-specific** logging configurations
- **Structured logging** with JSON output for production
- **Multiple handlers** (console, file, error file)
- **Logger hierarchy** for different components

## Data Layer Patterns

### Base Model Pattern

**Location**: `shared/base_model.py`

```python
class BaseModel(Base):
    """Abstract base model with common fields and utilities."""

    __abstract__ = True

    id: Mapped[int] = mapped_column(primary_key=True)
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now(), index=True
    )

    def to_dict(self) -> dict[str, Any]:
        """Convert model instance to dictionary."""
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }

    def update_from_dict(self, data: dict[str, Any]) -> None:
        """Update model instance from dictionary."""
        for key, value in data.items():
            if hasattr(self, key) and key not in ("id", "created_at"):
                setattr(self, key, value)
```

**Features**:
- **Common fields** (id, created_at, updated_at) for all models
- **Utility methods** for serialization and updates
- **Automatic timestamps** with database-level defaults
- **Indexed timestamps** for efficient querying

### Repository Pattern

**Example**: `exercises/repository.py`

```python
class ExerciseRepository:
    """Repository for exercise database operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, exercise_id: int) -> Exercise | None:
        """Get exercise by ID."""
        result = await self.session.get(Exercise, exercise_id)
        return result

    async def search(
        self, filters: ExerciseFilters, pagination: Pagination, user_id: int | None = None
    ) -> "Page[Exercise]":
        """Search exercises with filters and pagination."""
        # Complex search with permission filtering
        # Fuzzy matching for name searches
        # Efficient pagination

    async def create(self, exercise_data: dict) -> Exercise:
        """Create a new exercise."""
        exercise = Exercise(**exercise_data)
        self.session.add(exercise)
        await self.session.flush()  # Get ID without committing
        await self.session.refresh(exercise)
        return exercise
```

**Key Patterns**:
- **Session injection** through constructor
- **Async operations** with proper session management
- **Permission filtering** based on user context
- **Efficient querying** with appropriate indexing
- **Flush and refresh** pattern for getting IDs before commit

### Advanced Repository Features

#### Fuzzy Search Implementation
```python
async def _search_with_fuzzy_name_filter(self, name_query: str, ...) -> "Page[Exercise]":
    """Search exercises with fuzzy name matching for longer queries."""
    # Step 1: Get all candidates from database
    all_candidates = await self._get_candidates_from_db(...)

    # Step 2: Apply fuzzy filtering using rapidfuzz
    exercise_names = [ex.name for ex in all_candidates]
    fuzzy_results = process.extract(
        name_query, exercise_names,
        scorer=fuzz.partial_ratio, score_cutoff=70
    )

    # Step 3: Apply pagination to fuzzy results
    return self._paginate_fuzzy_results(fuzzy_results, pagination)
```

#### Permission-based Filtering
```python
def _build_permission_filter(self, user_id: int | None):
    """Build permission filtering clause."""
    if user_id is not None:
        return or_(
            Exercise.created_by_user_id == user_id,  # User's exercises
            ~Exercise.is_user_created,               # System exercises
        )
    return None
```

## Service Layer Patterns

### Service Structure

**Example**: `users/service.py`

```python
class UserService:
    """Service for user business logic."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repository = UserRepository(session)

    async def update_user_profile(
        self, user_id: int, update_data: UserProfileUpdate
    ) -> UserResponse:
        """Update user profile with validation."""
        try:
            # Business logic validation
            if "name" in update_dict:
                name = update_dict["name"].strip()
                if not name:
                    raise ValidationError("Name cannot be empty")
                update_dict["name"] = name

            # Repository operation
            updated_user = await self.repository.update(user_id, update_dict)

            # Convert to Pydantic BEFORE commit
            user_response = UserResponse.model_validate(updated_user)

            await self.session.commit()
            return user_response

        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error updating user profile {user_id}: {e}")
            raise
```

**Key Patterns**:
- **Repository composition** for data access
- **Transaction management** with commit/rollback
- **Validation logic** before repository operations
- **Pydantic conversion** within session context
- **Comprehensive error handling** with logging

### Service Best Practices

#### Data Conversion Pattern
```python
async def _workout_to_response(self, workout: Workout) -> WorkoutResponse:
    """Convert SQLAlchemy model to Pydantic response within session context."""
    # Extract all lazy-loaded attributes early to prevent issues
    exercise_executions = []
    for execution in workout.exercise_executions:
        # Process related data while session is active
        execution_response = await self._execution_to_response(execution)
        exercise_executions.append(execution_response)

    return WorkoutResponse(
        id=workout.id,
        finished_at=workout.finished_at,
        exercise_executions=exercise_executions,
        # ... other fields
    )
```

#### Error Handling Pattern
```python
async def business_operation(self, ...):
    """Standard error handling pattern for service methods."""
    try:
        # Validation
        await self._validate_business_rules(...)

        # Repository operations
        result = await self.repository.perform_operation(...)

        # Pydantic conversion
        response = ResponseModel.model_validate(result)

        # Commit transaction
        await self.session.commit()
        logger.info(f"Successfully completed operation")

        return response

    except ValidationError:
        # Business validation errors - don't rollback
        raise
    except Exception as e:
        # Unexpected errors - rollback and log
        await self.session.rollback()
        logger.error(f"Error in operation: {e}")
        raise
```

## Authentication & Security

### JWT Token Management

**Location**: `auth/jwt.py`

```python
class JWTManager:
    """JWT token management with access and refresh tokens."""

    def create_token_pair(self, user_id: int, email: str) -> TokenPair:
        """Create access and refresh token pair."""
        access_token = self._create_token(
            {"user_id": user_id, "email": email, "type": "access"},
            expires_delta=timedelta(minutes=self.access_token_expire_minutes)
        )
        refresh_token = self._create_token(
            {"user_id": user_id, "email": email, "type": "refresh"},
            expires_delta=timedelta(days=self.refresh_token_expire_days)
        )
        return TokenPair(access_token=access_token, refresh_token=refresh_token)

    def verify_token(self, token: str, expected_type: str) -> TokenData:
        """Verify JWT token and return token data."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            # Validation logic...
            return TokenData(user_id=payload["user_id"], email=payload["email"])
        except JWTError as e:
            raise AuthenticationError(f"Invalid token: {e}") from e
```

### Dependency Injection for Authentication

**Location**: `auth/dependencies.py`

```python
# Type aliases for clean dependency injection
CurrentUser = Annotated[User, Depends(get_current_user_from_token)]
OptionalUser = Annotated[User | None, Depends(get_current_user_optional)]
AdminUser = Annotated[User, Depends(get_current_admin_user)]

async def get_current_user_from_token(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(required_bearer_scheme)],
    session: Annotated[AsyncSession, Depends(get_session)],
    jwt_manager: Annotated[JWTManager, Depends(get_jwt_manager)],
) -> User:
    """Get current user from JWT token (required authentication)."""
    try:
        token_data = jwt_manager.verify_token(credentials.credentials, "access")
        user_repo = UserRepository(session)
        user = await user_repo.get_by_id(token_data.user_id)

        if not user or not user.is_active:
            raise HTTPException(status_code=401, detail="User not found")

        return user
    except AuthenticationError as e:
        raise HTTPException(status_code=401, detail=str(e)) from e
```

### Authentication Levels

1. **Required Authentication**: `CurrentUser` - Must have valid token
2. **Optional Authentication**: `OptionalUser` - Token optional, returns None if invalid
3. **Admin Authentication**: `AdminUser` - Requires valid token + admin privileges
4. **Token Only**: `TokenOnly` - Validates token without user lookup

## Router Layer Patterns

### Route Definition Pattern

```python
@router.post("/", response_model=WorkoutResponse, status_code=201)
async def create_workout(
    current_user: CurrentUser,
    workout_service: Annotated[WorkoutService, Depends(get_workout_service)],
) -> WorkoutResponse:
    """Create a new workout session."""
    try:
        return await workout_service.create_workout(current_user.id)
    except WorkoutAPIException as e:
        # Business exceptions are handled by global exception handlers
        raise
    except Exception as e:
        logger.error(f"Unexpected error creating workout: {e}")
        raise HTTPException(status_code=500, detail="Internal server error") from e
```

### Error Handling in Routes

**Global Exception Handlers** in `core/main.py`:

```python
@app.exception_handler(NotFoundError)
async def not_found_handler(request: Request, exc: NotFoundError):
    return JSONResponse(
        status_code=404,
        content={"detail": str(exc)}
    )

@app.exception_handler(ValidationError)
async def validation_error_handler(request: Request, exc: ValidationError):
    return JSONResponse(
        status_code=422,
        content={"detail": str(exc)}
    )
```

## Exception Hierarchy

**Location**: `shared/exceptions.py`

```python
class WorkoutAPIException(Exception):
    """Base exception for all workout API exceptions."""

class NotFoundError(WorkoutAPIException):
    """Raised when a requested resource is not found."""  # → HTTP 404

class ValidationError(WorkoutAPIException):
    """Raised when data validation fails."""              # → HTTP 422

class PermissionError(WorkoutAPIException):
    """Raised when user lacks permission."""              # → HTTP 403

class AuthenticationError(WorkoutAPIException):
    """Raised when authentication fails."""               # → HTTP 401

class BusinessRuleError(WorkoutAPIException):
    """Raised when a business rule is violated."""        # → HTTP 400
```

## Database Seeding System

### Base Seeder Pattern

**Location**: `seeding/base.py`

```python
class BaseSeeder(ABC):
    """Abstract base class for all database seeders."""

    def __init__(self, session, dry_run: bool = False, force: bool = False):
        self.session = session
        self.dry_run = dry_run
        self.force = force

    @abstractmethod
    async def seed(self) -> SeedResult:
        """Implement seeding logic in subclasses."""
        pass

    @abstractmethod
    def get_table_names(self) -> list[str]:
        """Return list of table names this seeder affects."""
        pass

    async def clean_tables(self) -> CleanResult:
        """Clean tables before seeding."""
        # Implementation with proper foreign key handling
```

### Seeder Registry

```python
class SeederRegistry:
    """Registry for managing and discovering seeders."""

    @classmethod
    def discover_seeders(cls) -> dict[str, type[BaseSeeder]]:
        """Automatically discover all seeder classes."""
        # Dynamic discovery of seeder implementations

    @classmethod
    def get_seeder_dependencies(cls) -> dict[str, list[str]]:
        """Get seeder dependency graph for proper ordering."""
        # Dependency resolution for seeding order
```

## Development Patterns & Best Practices

### Code Quality & Linting

The backend uses **Ruff** for both linting and formatting to maintain consistent code quality.

#### Import Organization
```python
# Correct import order (Ruff I001)
import logging
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response

from ..auth.dependencies import get_current_user_from_token
from ..users.models import User
from .dependencies import WorkoutServiceDep
from .schemas import (
    # Alphabetical order within groups
    ExerciseExecutionRequest,
    ExerciseExecutionResponse,
    WorkoutFinishResponse,
    WorkoutResponse,
)
```

**Best Practices**:
- **Standard library imports** first
- **Third-party imports** second
- **Local imports** last
- **Alphabetical ordering** within each group
- **Explicit imports** rather than import *

#### Import Placement in Tests
```python
# ✅ Correct: Imports at module level
from workout_api.workouts.schemas import ExerciseExecutionRequest

class TestWorkoutService:
    async def test_finish_workout_success(self, ...):
        # Use imported class directly
        execution_data = ExerciseExecutionRequest(...)

# ❌ Incorrect: Imports inside methods (PLC0415)
class TestWorkoutService:
    async def test_finish_workout_success(self, ...):
        from workout_api.workouts.schemas import ExerciseExecutionRequest  # Avoid this
        execution_data = ExerciseExecutionRequest(...)
```

**Best Practices**:
- **All imports at module level** - avoid local imports inside functions/methods
- **Group related imports** - use parentheses for multi-line imports
- **Avoid wildcard imports** - explicit imports improve code clarity

#### Whitespace and Formatting
```python
# ✅ Correct: No trailing whitespace
result = await workout_service.finish_workout(workout_id, user_id)

assert result is not None
assert isinstance(result, WorkoutResponse)

# ❌ Incorrect: Trailing whitespace (W293)
result = await workout_service.finish_workout(workout_id, user_id)
        # <- Trailing whitespace here
assert result is not None
```

**Best Practices**:
- **No trailing whitespace** on any lines, including blank lines
- **Consistent indentation** - use 4 spaces, no tabs
- **Blank line management** - use blank lines to separate logical sections

#### Common Linting Issues to Avoid

1. **Import Sorting (I001)**:
   ```python
   # ❌ Wrong order
   from fastapi import APIRouter
   import logging

   # ✅ Correct order
   import logging
   from fastapi import APIRouter
   ```

2. **Local Imports (PLC0415)**:
   ```python
   # ❌ Import inside function
   def some_function():
       from some_module import SomeClass

   # ✅ Import at module level
   from some_module import SomeClass

   def some_function():
       # Use SomeClass here
   ```

3. **Trailing Whitespace (W293)**:
   ```python
   # ❌ Blank line with spaces
   line_one = "content"
       # <- Spaces here
   line_two = "more content"

   # ✅ Clean blank line
   line_one = "content"

   line_two = "more content"
   ```

#### Linting Commands
```bash
# Check code quality
task lint

# Auto-fix issues where possible
task lint-fix

# Check only (no modifications)
uv run ruff check src tests scripts
uv run ruff format --check src tests scripts
```

### Model Definitions

```python
class Exercise(BaseModel):
    """Exercise model with proper typing and constraints."""

    __tablename__ = "exercises"

    # Use appropriate column types and constraints
    name: Mapped[str] = mapped_column(
        String(255), index=True, doc="Name of the exercise"
    )

    # Use enums for controlled vocabularies
    modality: Mapped[ExerciseModality] = mapped_column(
        Enum(ExerciseModality), index=True
    )

    # Proper foreign key relationships
    created_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id")
    )

    # Boolean fields with appropriate defaults
    is_user_created: Mapped[bool] = mapped_column(
        Boolean, default=True, index=True
    )
```

### Schema Definitions

```python
class ExerciseResponse(BaseModel):
    """Response schema with comprehensive field definitions."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    body_part: str
    modality: ExerciseModality
    picture_url: str | None = None
    is_user_created: bool
    created_by_user_id: int | None = None
    created_at: datetime
    updated_at: datetime

class ExerciseCreate(BaseModel):
    """Request schema with validation."""

    name: str = Field(..., min_length=1, max_length=255)
    body_part: str = Field(..., min_length=1, max_length=100)
    modality: ExerciseModality
    picture_url: HttpUrl | None = None
```

### Dependency Injection Patterns

```python
# Service factory pattern
def get_exercise_service(
    session: Annotated[AsyncSession, Depends(get_session)]
) -> ExerciseService:
    """Get ExerciseService with injected dependencies."""
    return ExerciseService(session)

# Repository injection
def get_workout_service(
    session: Annotated[AsyncSession, Depends(get_session)]
) -> WorkoutService:
    """Get WorkoutService with repository dependency."""
    repository = WorkoutRepository(session)
    return WorkoutService(repository, session)

# Type aliases for clean usage
ExerciseServiceDep = Annotated[ExerciseService, Depends(get_exercise_service)]
WorkoutServiceDep = Annotated[WorkoutService, Depends(get_workout_service)]
```

## Performance Considerations

### Database Optimization

1. **Indexing Strategy**:
   - Index frequently queried columns (timestamps, foreign keys)
   - Composite indexes for multi-column queries
   - Partial indexes for filtered queries

2. **Query Optimization**:
   - Use `select()` with explicit column selection when possible
   - Implement pagination for large result sets
   - Use fuzzy search only for complex queries

3. **Session Management**:
   - Convert to Pydantic models within session context
   - Use `flush()` and `refresh()` to get IDs before commit
   - Extract lazy-loaded attributes early to prevent `MissingGreenlet` errors

### Caching Patterns

```python
@lru_cache
def get_settings() -> Settings:
    """Cache settings for performance."""
    return Settings()

@lru_cache
def get_jwt_manager(settings: Settings) -> JWTManager:
    """Cache JWT manager instances."""
    return JWTManager(settings)
```

## Testing Integration

### Repository Testing
- Use real PostgreSQL with TestContainers
- Test permission filtering and complex queries
- Verify fuzzy search functionality

### Service Testing
- Use real repository dependencies
- Test business logic and validation
- Verify transaction handling

### Router Testing
- Full HTTP integration testing
- Test authentication and authorization
- Verify proper error responses

## Deployment Considerations

### Environment Configuration

```python
# Production settings
workers: int = 4
enable_http2: bool = True
keep_alive_timeout: int = 75

# Development settings
reload: bool = True
debug: bool = True
log_level: str = "DEBUG"
```

### Health Monitoring

```python
@router.get("/health")
async def health_check(
    db_manager: Annotated[DatabaseManager, Depends(get_db_manager)]
) -> dict:
    """Comprehensive health check endpoint."""
    return {
        "status": "healthy",
        "database": await db_manager.health_check(),
        "version": get_version(),
        "environment": settings.environment
    }
```

This architecture provides a solid foundation for a scalable, maintainable workout tracking API with clean separation of concerns, comprehensive error handling, and robust testing patterns.
