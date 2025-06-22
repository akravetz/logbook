# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

This project uses Task for development automation. Navigate to `backend/` directory first:

```bash
cd backend

# Core development workflow
task install              # Install dependencies (uv sync)
task run                  # Start development server
task test                 # Run tests
task test-cov            # Run tests with coverage
task lint                # Check code quality
task lint-fix            # Fix linting issues

# Database operations (when configured)
task migrate-new         # Generate new migration
task migrate-up          # Apply migrations
task db-reset           # Reset database (DESTRUCTIVE)

# Services
task docker-up          # Start PostgreSQL
task docker-down        # Stop services
task shell              # IPython shell with app context
```

## Testing

- Use `task test -- tests/specific_test.py` to run specific tests
- Use `task test -- -v -s` for verbose output and debugging
- Tests use testcontainers with real PostgreSQL database
- Each test runs in a transaction that's rolled back for isolation

## Code Quality

- **Linting**: Ruff is configured for fast linting and formatting
- **Type checking**: Run `task lint` after changes
- **Pre-commit hooks**: Automatically run quality checks on commit

## Architecture

### FastAPI Application Structure
- **Domain-based organization**: Code organized by business domain (auth, users, exercises, workouts)
- **Async-first**: All database operations and API endpoints are async
- **Repository pattern**: Clean separation between data access and business logic
- **Custom exception handling**: Centralized error handling in core/main.py:40-94

### Key Components
- `core/main.py`: FastAPI app with exception handlers and middleware
- `core/database.py`: Async SQLAlchemy session management
- `core/config.py`: Pydantic settings with .env support
- `shared/base_model.py`: SQLAlchemy base model
- `shared/exceptions.py`: Custom exception types

### Database
- **SQLAlchemy 2.0** with async support
- **PostgreSQL** as primary database
- **Atlas** for migrations (not Alembic)
- Connection pooling configured in database.py:11-17

## Development Patterns

### Adding New Features
1. Follow the domain structure: create new domains in `src/workout_api/`
2. Each domain should include: `models.py`, `schemas.py`, `service.py`, `router.py`
3. Register routers in `core/main.py`
4. Use the shared exception types from `shared/exceptions.py`

### Model Conventions
- Use SQLAlchemy 2.0 mapped column syntax
- Inherit from shared Base model
- Keep models focused on single domain

### Error Handling
- Use custom exceptions from `shared/exceptions.py`
- Exception handlers are configured in `core/main.py`
- Return appropriate HTTP status codes with consistent error format

## Technology Stack

- **Python 3.12+** with uv for package management
- **FastAPI** for web framework
- **SQLAlchemy 2.0** with async PostgreSQL
- **Pydantic v2** for validation and settings
- **pytest** with testcontainers for testing
- **Ruff** for linting and formatting
- **Atlas** for database migrations

## Environment Setup

- Copy `.env.example` to `.env` in backend directory
- Required variables: DATABASE_URL, SECRET_KEY
- Optional: GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET for OAuth