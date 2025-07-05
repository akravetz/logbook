# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Technology Stack

**Backend:** FastAPI (Python 3.12+) with PostgreSQL, SQLAlchemy async ORM, Google OAuth2 authentication
**Frontend:** Next.js 15 (TypeScript) with Tailwind CSS, shadcn/ui components, TanStack Query
**Package Management:** uv for Python, npm for Node.js
**Task Runner:** Task (Taskfile.yml) for backend operations

## Essential Commands

### Backend Development
```bash
task run                # Start development server (Hypercorn)
task test              # Run pytest test suite
task test-cov          # Run tests with coverage
task lint              # Check code quality (Ruff)
task lint-fix          # Auto-fix linting issues
task generate-openapi  # Generate OpenAPI spec
task db:migrate        # Apply database migrations
task docker-up         # Start PostgreSQL container
```

### Frontend Development
```bash
npm run dev            # Next.js development server
npm run dev:full       # Refresh API client + start dev server
npm run generate-api   # Generate TypeScript API client from OpenAPI
npm run refresh-api    # Update backend spec + regenerate client
npm run build          # Production build
npm run lint           # ESLint checks
```

### Testing
- Backend: `task test` (uses pytest with testcontainers for real PostgreSQL)
- Run single test: `task test -- tests/path/to/test.py::test_name`
- Test with coverage: `task test-cov` (generates HTML report in htmlcov/)

## Architecture

### Backend Structure
- **Domain-driven design** with Repository → Service → Router pattern
- **Core modules:** auth, users, exercises, workouts, health, voice
- **Base path:** `/api/v1/` with comprehensive OpenAPI documentation
- **Entry point:** `backend/src/workout_api/core/main.py`

### Frontend Structure
- **Next.js App Router** with TypeScript
- **Auto-generated API client** from OpenAPI spec (stored in `frontend/src/api/`)
- **Context-based state management** for auth and workout data
- **Component library:** shadcn/ui with Tailwind CSS

### Database Schema
- **Core entities:** Users, Exercises, Workouts, ExerciseExecutions, Sets
- **Key constraint:** Each exercise can only appear once per workout
- **Modalities:** Exercises support different types (DUMBBELL, BARBELL, etc.)

## Development Workflow

1. **API-first development:** Backend changes require `task generate-openapi`
2. **Frontend API sync:** Run `npm run refresh-api` after backend API changes
3. **Database changes:** Use Atlas migrations with `task db:migrate`
4. **Testing:** All tests run in transaction isolation with rollback
5. **Code quality:** Ruff for Python, ESLint for TypeScript

## Authentication
- **Google OAuth2** with JWT tokens and refresh capability
- **Development:** Requires Google OAuth app configuration
- **Session handling:** Secure middleware for OAuth flows

## Key Patterns
- **Async-first:** All database operations use async/await
- **Repository pattern:** Clean data access layer separation
- **Service layer:** Business logic isolated from API endpoints
- **Transaction isolation:** Each test runs independently
- **Type safety:** Full TypeScript coverage on frontend, Pydantic models on backend

Reference @docs/frontend.md when doing frontend development for design patterns and best practices
Reference @docs/backend.md when doing backend development for design patterns and best practices
Reference @docs/testing.md when doing backend test development for design patterns and best practices
