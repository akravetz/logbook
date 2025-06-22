# Python Backend Design Principles

This document outlines modern Python backend development principles and patterns that prioritize maintainability, testability, and developer experience.

## Core Technology Stack

### Package Management
- **Use `uv`** for Python environment management
  - Never edit `pyproject.toml` directly
  - Always use `uv add`, `uv run`, `uvx` commands
  - Fast, Rust-based, with deterministic dependency resolution

### Web Framework
- **FastAPI** with async/await everywhere
- **Pydantic v2** for data validation and settings
- **SQLAlchemy 2.0** with async support
- **PostgreSQL** as the primary database

### Development Tools
- **pytest** for testing (functional style with fixtures)
  - Never use unittest-style classes
  - Use `pytest-asyncio` for async tests
- **ruff** for linting and formatting
- **Atlas** for database migrations
  - Never use Alembic
  - Reference: https://atlasgo.io/guides/orms/sqlalchemy/script
- **Taskfile** for development command automation
- **pre-commit** hooks for code quality and security

### Testing Infrastructure
- **testcontainers** for real database testing
- Transaction isolation for test independence
- Shared session between API and database operations in tests

## Project Structure - Functional Cohesion

Organize code by business domain, not technical layers. Each module should contain all elements that contribute to a single well-defined business capability.

```
src/
└── <project_name>/
    ├── __init__.py
    ├── core/                # core logic
    │   ├── main.py          # FastAPI app entry
    │   ├── config.py        # Settings management
    │   └── database.py      # Database connection only
    ├── <domain>/            # Business domain (e.g., auth, users, orders)
    │   ├── __init__.py
    │   ├── models.py        # SQLAlchemy models for this domain
    │   ├── schemas.py       # Pydantic schemas for this domain
    │   ├── service.py       # Business logic
    │   ├── router.py        # API endpoints
    │   ├── repository.py    # Database queries (if complex)
    │   └── dependencies.py  # FastAPI dependencies
    └── shared/              # Truly shared utilities only
        ├── __init__.py
        ├── base_model.py    # SQLAlchemy Base
        └── exceptions.py    # Custom exceptions
```

This structure achieves:
- **Functional cohesion**: All code for a business concept in one place
- **High cohesion**: Related code stays together
- **Low coupling**: Domains interact through well-defined interfaces

## Development Automation

### Taskfile Setup

Create a `Taskfile.yml` for common development commands:

```yaml
version: '3'

vars:
  PYTHON: uv run python
  SRC_DIR: src
  TEST_DIR: tests

tasks:
  default:
    desc: List available tasks
    cmds:
      - task --list

  install:
    desc: Install dependencies
    cmds:
      - uv sync

  run:
    desc: Run the development server
    cmds:
      - uv run uvicorn {{.PROJECT_NAME}}.main:app --reload --host 0.0.0.0 --port ${PORT:-8000}

  test:
    desc: Run tests
    cmds:
      - uv run pytest {{.CLI_ARGS}}

  test-cov:
    desc: Run tests with coverage
    cmds:
      - uv run pytest --cov={{.SRC_DIR}} --cov-report=html --cov-report=term {{.CLI_ARGS}}

  lint:
    desc: Check code style and linting
    cmds:
      - uv run ruff check {{.SRC_DIR}} {{.TEST_DIR}}
      - uv run ruff format --check {{.SRC_DIR}} {{.TEST_DIR}}

  lint-fix:
    desc: Fix linting issues and format code
    cmds:
      - uv run ruff check {{.SRC_DIR}} {{.TEST_DIR}} --fix
      - uv run ruff format {{.SRC_DIR}} {{.TEST_DIR}}

  migrate-new:
    desc: Generate new migration
    cmds:
      - uv run atlas migrate diff --env sqlalchemy

  migrate-up:
    desc: Apply migrations
    cmds:
      - uv run atlas migrate apply --env sqlalchemy --url ${DATABASE_URL}

  migrate-down:
    desc: Rollback last migration
    cmds:
      - uv run atlas migrate down --env sqlalchemy --url ${DATABASE_URL}

  db-reset:
    desc: Reset database (WARNING destructive)
    cmds:
      - echo "Dropping and recreating database..."
      - task: migrate-down -- --amount 9999
      - task: migrate-up

  shell:
    desc: Start IPython shell with app context
    cmds:
      - uv run ipython -i -c "from {{.PROJECT_NAME}}.main import *"

  docker-up:
    desc: Start docker services
    cmds:
      - docker-compose up -d postgres redis

  docker-down:
    desc: Stop docker services
    cmds:
      - docker-compose down

  pre-commit:
    desc: Run pre-commit hooks
    cmds:
      - pre-commit run --all-files
```

### Pre-commit Configuration

Create `.pre-commit-config.yaml` for automated code quality checks:

```yaml
default_language_version:
  python: python3.11

repos:
  # Security - detect secrets
  - repo: https://github.com/gitleaks/gitleaks
    rev: v8.18.0
    hooks:
      - id: gitleaks

  # Python formatting and linting
  - repo: local
    hooks:
      - id: ruff-format
        name: Ruff Format
        entry: uv run ruff format
        language: system
        types: [python]
        pass_filenames: true

      - id: ruff-lint
        name: Ruff Lint
        entry: uv run ruff check --fix
        language: system
        types: [python]
        pass_filenames: true

  # General file checks
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
        args: ['--maxkb=1000']
      - id: check-json
      - id: check-toml
      - id: check-merge-conflict
      - id: debug-statements
      - id: mixed-line-ending

  # Markdown
  - repo: https://github.com/igorshubovych/markdownlint-cli
    rev: v0.37.0
    hooks:
      - id: markdownlint
        args: ['--fix']
```

Create `pyproject.toml` configuration for Ruff:

```toml
[tool.ruff]
target-version = "py311"
line-length = 88
select = [
    "E",   # pycodestyle errors
    "W",   # pycodestyle warnings
    "F",   # pyflakes
    "I",   # isort
    "B",   # flake8-bugbear
    "C4",  # flake8-comprehensions
    "UP",  # pyupgrade
    "ARG", # flake8-unused-arguments
    "SIM", # flake8-simplify
]
ignore = [
    "E501",  # line too long (handled by formatter)
    "B008",  # do not perform function calls in argument defaults
]

[tool.ruff.isort]
known-third-party = ["fastapi", "pydantic", "sqlalchemy"]

[tool.ruff.per-file-ignores]
"__init__.py" = ["F401"]  # unused imports in __init__ files
```

### Setup Instructions

```bash
# Install task runner
sh -c "$(curl --location https://taskfile.dev/install.sh)" -- -d

# Install pre-commit
uv add --dev pre-commit

# Setup pre-commit hooks
pre-commit install

# Optional: Run against all files
pre-commit run --all-files
```

## Configuration Management

Use Pydantic Settings with `.env` files for type-safe configuration:

```python
# config.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

class Settings(BaseSettings):
    # Application settings
    app_name: str = "API"
    environment: str = "development"
    debug: bool = False
    
    # Database
    database_url: str
    
    # Security
    secret_key: str
    
    # Add other settings as needed
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )
    
    @property
    def database_url_async(self) -> str:
        """Convert sync PostgreSQL URL to async"""
        return str(self.database_url).replace(
            "postgresql://", 
            "postgresql+asyncpg://"
        )

@lru_cache()
def get_settings() -> Settings:
    return Settings()
```

Always provide `.env.example` with all required variables documented.

## Database Patterns

### Async SQLAlchemy Setup
```python
# database.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base

Base = declarative_base()

engine = create_async_engine(
    settings.database_url_async,
    pool_pre_ping=True,
)

async def get_db():
    async with AsyncSession(engine) as session:
        yield session
```

### Model Organization
- One model file per domain
- Use SQLAlchemy 2.0 mapped column syntax
- Keep relationships explicit

### Migration Strategy
Use Atlas for schema migrations:

1. Create `scripts/load_models.py`:
```python
from <project>.models import *  # Import all models
from atlas_provider_sqlalchemy.ddl import print_ddl

print_ddl("postgresql", [Model1, Model2, ...])
```

2. Configure `atlas.hcl`:
```hcl
data "external_schema" "sqlalchemy" {
    program = ["python3", "scripts/load_models.py"]
}

env "sqlalchemy" {
    src = data.external_schema.sqlalchemy.url
    dev = "docker://postgres/16/dev?search_path=public"
    migration {
        dir = "file://migrations"
    }
}
```

## API Design Principles

### RESTful Patterns
- Use proper HTTP methods (GET, POST, PATCH, DELETE)
- Nest resources appropriately (e.g., `/resources/{id}/sub-resources`)
- Return appropriate status codes
- Consistent error responses

### Schema Separation
Maintain separate Pydantic schemas for:
- Request bodies (Create, Update)
- Response models
- Internal data transfer

This separation allows API evolution without database changes.

## Testing Philosophy

### Transaction Isolation Pattern
Every test runs in a transaction that's rolled back after completion:

```python
# conftest.py
@pytest_asyncio.fixture
async def connection(engine):
    async with engine.connect() as conn:
        async with conn.begin() as trans:
            yield conn
            await trans.rollback()

@pytest_asyncio.fixture
async def session(connection):
    async with AsyncSession(
        bind=connection,
        join_transaction_mode="create_savepoint"
    ) as session:
        yield session

@pytest_asyncio.fixture
def override_get_db(session):
    app.dependency_overrides[get_db] = lambda: session
    yield
    app.dependency_overrides.clear()
```

This ensures:
- Complete test isolation
- API and database operations share the same transaction
- Fast test execution (no schema recreation)

### Test Organization
- Group tests by business domain
- Use fixtures for common setup
- Test both happy paths and error cases
- Integration tests should test complete flows

## Async Best Practices

1. **Use async everywhere** - from database queries to API endpoints
2. **Avoid blocking operations** - use async libraries for I/O
3. **Proper connection management** - use connection pooling
4. **Concurrent operations** - use `asyncio.gather()` when appropriate

## Development Workflow

With Taskfile setup, common commands become:

```bash
# Initial setup
task install
task docker-up

# Development
task run

# Testing
task test
task test-cov

# Code quality
task lint
task lint-fix

# Migrations
task migrate-new
task migrate-up

# Pre-commit
task pre-commit
```

## Security Considerations

1. **Environment Variables** - Never commit secrets (enforced by gitleaks)
2. **Input Validation** - Use Pydantic for all inputs
3. **SQL Injection** - Use SQLAlchemy's query builder
4. **Authentication** - Implement proper auth flows
5. **CORS** - Configure appropriately for your frontend
6. **Secret Scanning** - Pre-commit hooks prevent accidental commits

### Gitleaks Configuration

Create `.gitleaks.toml` for custom rules:

```toml
[extend]
# Extend the base configuration

[[rules]]
description = "Database URL with password"
regex = '''postgresql://[^:]*:[^@]*@'''
tags = ["database", "credentials"]

[[rules]]
description = "Private key"
regex = '''-----BEGIN (RSA|EC|DSA|OPENSSH) PRIVATE KEY-----'''
tags = ["key", "private"]

[allowlist]
paths = [
    ".env.example",
    "docs/",
]
```

## Performance Guidelines

1. **Database Queries**
   - Use eager loading to avoid N+1 queries
   - Index foreign keys and commonly queried fields
   - Use database connection pooling

2. **Caching**
   - Consider Redis for session storage and caching
   - Cache expensive computations
   - Use ETags for HTTP caching

3. **Pagination**
   - Always paginate list endpoints
   - Use cursor-based pagination for large datasets

## Documentation

1. **API Documentation** - FastAPI generates OpenAPI specs automatically
2. **Code Documentation** - Document complex business logic
3. **README** - Include setup instructions and architecture overview
4. **Type Hints** - Use throughout for better IDE support

## Monitoring and Observability

1. **Structured Logging** - Use JSON logging in production
2. **Health Checks** - Implement `/health` endpoint
3. **Metrics** - Track request duration, error rates
4. **Tracing** - Consider OpenTelemetry for distributed tracing

## Deployment Considerations

1. **Containerization** - Use Docker for consistent deployments
2. **Environment Parity** - Keep dev/staging/prod similar
3. **Database Migrations** - Run migrations separately from app startup
4. **Graceful Shutdown** - Handle SIGTERM properly

## Anti-Patterns to Avoid

1. **Circular Imports** - Keep dependencies unidirectional
2. **Business Logic in Routes** - Use service layer
3. **Mutable Default Arguments** - Use `Field(default_factory=list)`
4. **Synchronous Operations in Async Context** - Use async versions
5. **Global State** - Use dependency injection
6. **Secrets in Code** - Use environment variables (enforced by pre-commit)

## Example Implementation

A complete domain module following these principles:

```python
# users/models.py
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column
from shared.base_model import Base

class User(Base):
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True)
    name: Mapped[str] = mapped_column(String(100))

# users/schemas.py
from pydantic import BaseModel, EmailStr

class UserCreate(BaseModel):
    email: EmailStr
    name: str

class UserResponse(BaseModel):
    id: int
    email: str
    name: str
    
    model_config = {"from_attributes": True}

# users/service.py
from sqlalchemy.ext.asyncio import AsyncSession
from .models import User
from .schemas import UserCreate, UserResponse

class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_user(self, data: UserCreate) -> User:
        user = User(**data.model_dump())
        self.db.add(user)
        await self.db.commit()
        return user

# users/router.py
from fastapi import APIRouter, Depends
from .service import UserService
from .schemas import UserCreate, UserResponse

router = APIRouter()

@router.post("/", response_model=UserResponse)
async def create_user(
    data: UserCreate,
    service: UserService = Depends(get_user_service)
):
    user = await service.create_user(data)
    return UserResponse.model_validate(user)
```

## Quick Start Checklist

- [ ] Install `uv` for package management
- [ ] Install `task` for command automation
- [ ] Copy Taskfile.yml to project root
- [ ] Copy .pre-commit-config.yaml to project root
- [ ] Run `task install` to setup dependencies
- [ ] Run `pre-commit install` to setup git hooks
- [ ] Copy .env.example to .env and fill in values
- [ ] Run `task docker-up` for local services
- [ ] Run `task migrate-up` to setup database
- [ ] Run `task run` to start development

This design philosophy prioritizes:
- **Maintainability** through clear organization
- **Security** through automated secret scanning
- **Developer Experience** through automation and type safety
- **Code Quality** through automated formatting and linting
- **Testability** through dependency injection and isolation
- **Performance** through async operations
``` 