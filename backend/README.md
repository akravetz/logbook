# Workout API

A FastAPI-based workout tracking API built with modern Python patterns.

## Quick Start

### Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) for package management
- [Task](https://taskfile.dev/) for development automation
- Docker (for local PostgreSQL)

### Setup

1. **Install uv and Task**
   ```bash
   # Install uv
   curl -LsSf https://astral.sh/uv/install.sh | sh

   # Install Task (macOS)
   brew install go-task/tap/go-task
   # For other platforms: https://taskfile.dev/installation/
   ```

2. **Clone and setup project**
   ```bash
   cd backend
   uv sync                    # Install all dependencies
   cp .env.example .env       # Create environment file
   # Edit .env with your settings
   ```

3. **Start local services**
   ```bash
   task docker-up            # Start PostgreSQL
   ```

4. **Setup pre-commit hooks**
   ```bash
   task pre-commit           # Install git hooks
   ```

### Development

```bash
# Available commands
task                      # List all available tasks

# Development workflow
task run                  # Start development server
task test                 # Run tests
task lint                 # Check code quality
task lint-fix             # Fix linting issues

# Database management (when Atlas is configured)
task migrate-new          # Generate new migration
task migrate-up           # Apply migrations
task db-reset             # Reset database (DESTRUCTIVE)

# Utilities
task shell                # Start IPython shell
task docker-up            # Start services
task docker-down          # Stop services
```

## Architecture

### Project Structure

```
backend/
├── src/workout_api/           # Main application package
│   ├── core/                  # Core infrastructure
│   │   ├── config.py         # Settings management
│   │   ├── database.py       # Database connection
│   │   └── main.py           # FastAPI app
│   ├── shared/               # Shared utilities
│   │   ├── base_model.py     # SQLAlchemy base
│   │   ├── exceptions.py     # Custom exceptions
│   │   └── schemas.py        # Common schemas
│   ├── auth/                 # Authentication domain
│   ├── users/                # User management domain
│   ├── exercises/            # Exercise management domain
│   └── workouts/             # Workout tracking domain
├── tests/                    # Test suite
├── migrations/               # Database migrations
└── scripts/                  # Utility scripts
```

### Design Principles

- **Functional Cohesion**: Code organized by business domain
- **Async First**: All I/O operations are async
- **Repository Pattern**: Clean separation of data access
- **Service Layer**: Business logic isolated from API endpoints
- **Transaction Isolation**: Tests run in rolled-back transactions

## API Documentation

Once running, visit:
- **Interactive Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
# Database
DATABASE_URL=postgresql://workout_user:workout_pass@localhost:5432/workout_db

# Security
SECRET_KEY=your-secret-key-here
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret

# Application
ENVIRONMENT=development
DEBUG=true
```

## Testing

```bash
# Run all tests
task test

# Run with coverage
task test-cov

# Run specific test file
task test -- tests/test_main.py

# Debug tests with verbose output
task test -- -v -s
```

Tests use:
- **testcontainers**: Real PostgreSQL database
- **Transaction isolation**: Each test runs in a rolled-back transaction
- **FastAPI TestClient**: Full integration testing

## Code Quality

```bash
# Check code quality
task lint

# Auto-fix issues
task lint-fix

# Run pre-commit hooks manually
task pre-commit
```

Includes:
- **Ruff**: Fast Python linter and formatter
- **Gitleaks**: Secret detection
- **Pre-commit hooks**: Automatic quality checks

## Deployment

TODO: Add deployment instructions once infrastructure is set up.

## Development Notes

- Never edit `pyproject.toml` directly - use `uv add`/`uv remove`
- Follow the Repository → Service → Router pattern for new features
- All database operations must be async
- **Always use bulk/batch operations** instead of row-by-row operations when working with databases
- Use the shared exception types for consistent error handling
- Write tests for all new features

## Contributing

1. Follow the established patterns in `docs/backend_design.md`
2. Ensure all tests pass: `task test`
3. Check code quality: `task lint`
4. Update documentation as needed

## API Reference

See the generated OpenAPI documentation at `/docs` when running the server.
