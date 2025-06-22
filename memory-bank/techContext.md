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
task dev       # Run development server
task test      # Run all tests
task lint      # Run linting
task migrate   # Run database migrations
task db:reset  # Reset database
```

### Testing Strategy
- **Unit Tests**: Business logic in services
- **Integration Tests**: API endpoints with real database
- **Test Isolation**: Transaction rollback pattern
- **Test Database**: testcontainers PostgreSQL
- **Fixtures**: pytest fixtures for common data

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