# Tech Context

## Technology Stack

### Frontend (Future)
- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript
- **UI Library**: ShadCN (Radix UI + Tailwind CSS)
- **State Management**: TBD (likely Zustand or Context)
- **API Client**: TBD
- **Build Tool**: Next.js built-in (Turbopack)

### Backend (Current Focus)
- **Language**: Python 3.12+
- **Framework**: FastAPI (async)
- **Database**: PostgreSQL
- **ORM**: SQLAlchemy 2.0 (with async)
- **Validation**: Pydantic 2
- **Package Manager**: uv
- **Migrations**: Atlas
- **Testing**: pytest + testcontainers
- **Linting**: ruff
- **Security**: pre-commit + gitleaks

### Infrastructure
- **Deployment**: TBD
- **Database**: PostgreSQL (managed service)
- **File Storage**: TBD (likely S3-compatible)
- **Authentication**: Google SSO via OAuth2
- **Monitoring**: TBD

### Development Tools
- **Package Manager**: pnpm
- **Linting**: ESLint with strict config
- **Formatting**: Prettier
- **Git Hooks**: Husky + lint-staged
- **CI/CD**: GitHub Actions

## Development Setup

### Prerequisites
```bash
node >= 18.x
pnpm >= 8.x
```

### Environment Variables
```env
NEXT_PUBLIC_API_URL=http://localhost:3000/api/v1
GOOGLE_CLIENT_ID=xxx
GOOGLE_CLIENT_SECRET=xxx
```

### Key Dependencies
```json
{
  "next": "^14.0.0",
  "react": "^18.2.0",
  "typescript": "^5.0.0",
  "@tanstack/react-query": "^5.0.0",
  "tailwindcss": "^3.3.0",
  "react-hook-form": "^7.0.0",
  "zod": "^3.0.0",
  "msw": "^2.0.0"
}
```

## Development Environment

### Required Tools
- **Python**: 3.12+
- **uv**: Latest version for package management
- **Docker**: For testcontainers and local PostgreSQL
- **Atlas**: For database migrations
- **Task**: For command automation

### Environment Setup
```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install Task
brew install go-task/tap/go-task  # macOS
# or see: https://taskfile.dev/installation/

# Clone and setup
git clone <repo>
cd workout-api
uv venv
uv pip install -e ".[dev]"
pre-commit install
```

### Configuration
All configuration via environment variables:
- `.env` for local development
- `.env.test` for test overrides
- Never commit secrets - gitleaks prevents this

## Development Workflow

### Task Commands
```bash
task dev         # Run development server
task test        # Run all tests
task lint        # Run linting
task db:migrate  # Apply database migrations
task db:status   # Check migration status
task db:diff     # Generate new migration
task db:reset    # Reset database
```

### Testing Strategy (Updated)
- **Unit Tests**: Business logic in services (69+ service tests)
- **Integration Tests**: API endpoints with real database (26+ router tests)
- **Repository Tests**: Database operations with complex queries (26+ repository tests)
- **Test Isolation**: Transaction rollback with savepoints - perfect isolation
- **Test Database**: PostgreSQL testcontainers for realistic testing
- **Modern Async**: pytest-anyio for better async handling
- **Authentication Testing**: Dependency injection patterns instead of patching

#### ⚠️ CRITICAL: Pytest Fixture Patterns
**NEVER remove fixture parameters from test functions - they are always used for test setup**

```python
# ✅ CORRECT: Fixtures create test data even if not directly referenced
async def test_user_statistics(
    self, authenticated_client: AsyncClient, test_user: User  # noqa: ARG002
):
    """The test_user fixture creates a user in the database for authentication."""
    response = await authenticated_client.get("/api/v1/users/me/stats")
    assert response.status_code == 200

# ❌ WRONG: Removing fixtures breaks test setup
async def test_user_statistics(self, authenticated_client: AsyncClient):
    """Without test_user fixture, authenticated_client has no user to authenticate!"""
    response = await authenticated_client.get("/api/v1/users/me/stats")  # Will fail
```

**Fixture Usage Rules:**
- Fixtures perform setup even when not directly referenced in test code
- Use `# noqa: ARG002` to suppress "unused argument" warnings for fixtures
- Common fixtures: `test_user`, `sample_workout`, `authenticated_client`, `session`
- Never remove fixture parameters to "fix" linting warnings

### Code Quality
- **Pre-commit Hooks**: Format, lint, security checks
- **Type Checking**: Pydantic enforces at runtime
- **Linting**: ruff for fast Python linting
- **Security**: gitleaks prevents secret commits

## Technical Decisions

### Why These Choices

#### uv over pip/poetry
- Extremely fast dependency resolution
- Built in Rust for performance
- Modern replacement for pip-tools
- Simpler than poetry for our needs

#### FastAPI + Async
- Native async support for performance
- Automatic OpenAPI documentation
- Pydantic integration for validation
- Modern Python patterns

#### SQLAlchemy 2.0 + Pydantic
- Clear separation of concerns
- SQLAlchemy for powerful ORM features
- Pydantic for API validation
- Better than SQLModel for complex apps

#### Atlas over Alembic
- Modern migration tool
- Better schema drift detection
- Declarative migrations
- Cloud-native approach

#### testcontainers
- Real database in tests
- No mocking complexity
- Catches real SQL issues
- Better than SQLite for tests

### Performance Considerations
- Async everywhere for I/O operations
- Connection pooling for database
- Proper pagination for large datasets
- Indexed database queries

### Security Approach
- Environment variables for secrets
- Pre-commit hooks prevent leaks
- SQL injection prevention via ORM
- Input validation via Pydantic
- Authentication via OAuth2

## Constraints

### Technical Constraints
- Python 3.12+ required (for latest features)
- PostgreSQL 15+ (for modern SQL features)
- Must support async operations throughout
- API must be RESTful (no GraphQL for v1)

### Development Constraints
- All code must pass pre-commit hooks
- Tests required for new features
- Documentation for public APIs
- Follow functional cohesion structure

## Current Implementation Status

### ✅ Completed Modules
- **User Management**: Full CRUD with JWT/OAuth authentication (41 tests)
- **Exercise Management**: Complete CRUD with search, filtering, pagination (69 tests)
- **Database Schema**: Deployed with Atlas migrations (5 tables with relationships)
- **Testing Infrastructure**: 171 tests passing with modern async patterns

### 🚧 In Progress
- **Workout Management**: Next major module (0% complete)

### 📋 Architecture Patterns Established
- Service layer returns Pydantic models (prevents session issues)
- Repository layer handles database operations
- Router layer uses Pydantic directly (no .model_validate())
- Dependency injection for all services and testing
- Route ordering for FastAPI (specific before generic)
- Mixed authentication (public read, protected write)

## Future Considerations
- WebSocket support for real-time features
- Redis for caching/sessions
- Background job processing (Celery/Arq)
- Full-text search (PostgreSQL or Elasticsearch)
- Mobile app API requirements

## Technical Constraints

### Performance Requirements
- Initial load: < 3s on 4G
- Interaction response: < 100ms
- API response: < 500ms
- Bundle size: < 200KB gzipped

### Browser Support
- Chrome/Edge: Last 2 versions
- Safari: Last 2 versions
- Firefox: Last 2 versions
- Mobile: iOS 14+, Android 10+

### Accessibility
- WCAG 2.1 AA compliance
- Keyboard navigation
- Screen reader support
- High contrast mode

### Security
- HTTPS only
- Content Security Policy
- XSS protection
- CSRF tokens
- Rate limiting

## Critical SQLAlchemy ORM Patterns

### ⚠️ CRITICAL: ORM Delete Operations vs Raw SQL
**NEVER use raw SQL DELETE for operations involving foreign key relationships**

#### ❌ WRONG: Raw SQL bypasses cascade behavior
```python
# This causes foreign key constraint violations
delete_stmt = delete(ExerciseExecution).where(
    ExerciseExecution.id == execution_id
)
result = await session.execute(delete_stmt)
return result.rowcount > 0
```

#### ✅ CORRECT: ORM operations respect cascade relationships
```python
# This properly triggers cascade="all, delete-orphan"
execution_stmt = select(ExerciseExecution).where(
    ExerciseExecution.id == execution_id
)
result = await session.execute(execution_stmt)
execution = result.scalar_one_or_none()

if not execution:
    return False

# Use ORM delete - triggers SQLAlchemy cascades
await session.delete(execution)
await session.flush()           # Ensure deletion visible within transaction
session.expire_all()           # Clear cached relationships (synchronous!)
return True
```

### Why This Pattern is Critical
1. **Cascade Behavior**: Raw SQL DELETE bypasses SQLAlchemy's `cascade="all, delete-orphan"` settings
2. **Foreign Key Constraints**: Database constraints prevent deletion when related records exist
3. **Cache Issues**: SQLAlchemy caches relationship queries, showing stale data after deletion
4. **Transaction Visibility**: `flush()` ensures changes are visible within the same transaction
5. **Cache Invalidation**: `expire_all()` clears cached relationships to prevent stale reads

### Foreign Key Constraint Resolution Pattern
```python
async def delete_with_cascade(session: AsyncSession, model_class, object_id: int) -> bool:
    """Safe deletion pattern that respects SQLAlchemy cascades."""
    # Get the object first
    stmt = select(model_class).where(model_class.id == object_id)
    result = await session.execute(stmt)
    obj = result.scalar_one_or_none()

    if not obj:
        return False

    # Use ORM delete (not raw SQL)
    await session.delete(obj)

    # Ensure changes are visible and clear cache
    await session.flush()       # Makes deletion visible in transaction
    session.expire_all()        # Clears cached relationships (sync call!)

    return True
```

### Cache Management Rules
- **`session.flush()`**: Async call that pushes changes to database within transaction
- **`session.expire_all()`**: Synchronous call that clears SQLAlchemy's identity map
- **Order matters**: Always flush before expire_all
- **Transaction scope**: Both operations work within the current transaction

### Critical Database Transaction Patterns

#### ⚠️ Service Layer Transaction Responsibility
**The session dependency does NOT auto-commit transactions. Transaction management is the service layer's responsibility.**

```python
# ✅ CORRECT: Service layer handles commits
class UserService:
    async def update_user_profile(self, user_id: int, data: dict) -> UserResponse:
        updated_user = await self.repository.update(user_id, data)
        user_response = UserResponse.model_validate(updated_user)
        await self.session.commit()  # Explicit commit
        return user_response

# ❌ WRONG: Depending on automatic commits
class UserService:
    async def update_user_profile(self, user_id: int, data: dict) -> UserResponse:
        updated_user = await self.repository.update(user_id, data)
        # Missing commit - changes would be lost!
        return UserResponse.model_validate(updated_user)
```

#### Transaction Boundary Guidelines
1. **Complete Units of Work**: Commit only when entire business operation is complete
2. **Error Handling**: Always rollback on exceptions in service methods
3. **Session Dependency**: Only provides session, handles cleanup and rollback on errors
4. **Multiple Operations**: Commit after all related changes in a single transaction

#### Example Service Pattern
```python
class WorkoutService:
    async def create_workout_with_exercises(self, user_id: int, data: WorkoutCreate):
        try:
            # Multiple related operations in one transaction
            workout = await self.repository.create_workout(user_id)
            for exercise_data in data.exercises:
                await self.repository.create_exercise_execution(workout.id, exercise_data)

            # Convert to response models before commit
            response = WorkoutResponse.model_validate(workout)

            # Commit entire unit of work
            await self.session.commit()
            return response

        except Exception as e:
            await self.session.rollback()  # Rollback on any error
            raise ServiceError("Failed to create workout") from e
```

#### Session Dependency Implementation
```python
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Provides session with cleanup - NO automatic commits."""
    async with session_maker() as session:
        try:
            yield session  # Service layer manages commits
        except Exception as e:
            await session.rollback()  # Auto-rollback on errors
            raise
        finally:
            await session.close()  # Always cleanup
```
