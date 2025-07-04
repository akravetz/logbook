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

# Database Seeding (Production-Ready)
task seed                    # Run all seeders
task seed:exercises         # Seed exercises only
task seed:list              # List available seeders
task seed:prod              # Seed production database (requires DATABASE_URL)
task seed -- --dry-run     # Preview seeding operations
task seed -- --force       # Force re-seeding of existing items
task seed -- --verbose     # Detailed progress logging

# OpenAPI Generation (Optimized)
task generate-openapi    # Generate OpenAPI spec directly to frontend/openapi.json
```

### Frontend Development
```bash
npm run dev              # Start Next.js development server
npm run refresh-api      # Regenerate API types (calls backend generate-openapi)
npm run generate-api     # Generate TypeScript types from OpenAPI spec
npm run build           # Build for production
npm run dev:full        # Refresh API and start dev server
```

### Development Authentication (Latest)
**Two authentication options available in development:**

1. **Development Login** (Recommended for local dev):
   - Available only when `NODE_ENV=development`
   - Login with any email address
   - No Google OAuth setup required
   - Creates users with "dev:" prefix to prevent conflicts

2. **Google OAuth** (Production-ready):
   - Requires `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET`
   - Full production OAuth flow
   - Same as production authentication

**Setup for Development:**
```bash
# Option 1: Use dev login (zero setup)
NODE_ENV=development npm run dev
# Login screen will show "Dev Login" option

# Option 2: Use Google OAuth (requires credentials)
# Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in .env.local
npm run dev
```

### Database Seeding Workflow (Production-Ready)
**Comprehensive seeding system for all environments:**
```bash
# Development seeding
task seed:exercises              # Seed exercises from CSV
task seed:exercises -- --dry-run # Preview what would be seeded
task seed:exercises -- --force   # Re-seed existing exercises

# Production seeding (requires confirmation)
task seed:prod -- --database-url $DATABASE_URL

# Multi-environment seeding
task seed -- --database-url postgresql://user:pass@host:5432/db
```

**Key Features:**
- ✅ **Production Safety**: Mandatory confirmation for production environments
- ✅ **Dry Run Mode**: Preview operations without making database changes
- ✅ **Force Mode**: Override existing item checks for re-seeding scenarios
- ✅ **Progress Tracking**: Real-time progress updates and detailed reporting
- ✅ **Error Handling**: Graceful failure handling with comprehensive error reporting
- ✅ **Extensible**: Registry pattern for adding new seeder types

**Seeding Architecture:**
```mermaid
graph TD
    A[CLI Script] --> B[Parse Arguments]
    B --> C[Initialize Database]
    C --> D[Load Seeders]
    D --> E{Dry Run?}
    E -->|Yes| F[Preview Operations]
    E -->|No| G[Execute Seeding]
    F --> H[Report Results]
    G --> I[Track Progress]
    I --> H
    H --> J[Summary Output]
```

### OpenAPI Workflow (Optimized)
**Streamlined generation process:**
```bash
# Single command regenerates everything
npm run refresh-api

# What it does:
# 1. Backend: Generate OpenAPI spec → frontend/openapi.json
# 2. Frontend: Generate TypeScript types from openapi.json
```

**Key Improvements:**
- ✅ No file duplication (single openapi.json in frontend)
- ✅ Simplified workflow (50% fewer steps)
- ✅ No sync issues between backend/frontend copies
- ✅ Version control friendly (no accidental backend commits)

### Testing Strategy (Updated)
- **Unit Tests**: Business logic in services (93+ authentication tests)
- **Integration Tests**: API endpoints with real database (26+ router tests)
- **Repository Tests**: Database operations with complex queries (26+ repository tests)
- **Test Isolation**: Transaction rollback with savepoints - perfect isolation
- **Test Database**: PostgreSQL testcontainers for realistic testing
- **Modern Async**: pytest-anyio for better async handling
- **Authentication Testing**: FastAPI dependency injection instead of patching
- **Development Auth Testing**: Environment-based availability and security testing

#### ⚠️ CRITICAL: Test Patterns
**FastAPI Dependency Injection in Tests:**
```python
# ✅ CORRECT: Use dependency overrides
@pytest.fixture
def mock_auth_service():
    service = Mock(spec=AuthService)
    service.authenticate_with_dev_login = AsyncMock(return_value=mock_response)
    return service

async def test_dev_login(client: AsyncClient, mock_auth_service):
    app.dependency_overrides[get_auth_service_dependency()] = lambda: mock_auth_service
    response = await client.post("/api/v1/auth/dev-login", json={"email": "test@example.com"})

# ❌ WRONG: Patching breaks dependency injection
async def test_dev_login(client: AsyncClient):
    with patch('auth.router.AuthService') as mock_service:
        # Breaks FastAPI dependency system
```

**Import Organization:**
```python
# ✅ CORRECT: All imports at module level
from workout_api.auth.schemas import DevLoginRequest, DevLoginResponse
from workout_api.auth.service import AuthService

# ❌ WRONG: Imports inside functions
async def dev_login(request, auth_service):
    from workout_api.auth.schemas import DevLoginRequest  # Violates conventions
```

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
