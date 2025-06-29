# Project Brief: Workout Tracking App

## Overview
A workout tracking web application focused on simplicity and efficiency for gym use. Users can log their workouts, track exercises, and monitor progress over time.

## Core Requirements

### Must Have (MVP)
1. **User Management**
   - Google SSO authentication only
   - User profile with basic info
   - Personal exercise library

2. **Exercise Management**
   - Browse system exercise database
   - Create custom exercises
   - Search by name, category, modality
   - Track: name, category, body parts, modality

3. **Workout Tracking**
   - Start/finish workouts
   - Add exercises to workout (one per workout)
   - Log sets with reps and weight
   - Maintain exercise order
   - View workout history

4. **Basic Analytics**
   - Total workouts completed
   - Favorite exercises
   - Personal records

### Nice to Have (Future)
- Workout templates
- Progress graphs
- Rest timers
- Exercise videos/images
- Social features
- Offline support
- Mobile app

## Technical Approach

### Development Strategy
**Backend-first approach** - Build and test the API before creating the frontend interface.

### Backend Stack
- **Language**: Python 3.12+
- **Framework**: FastAPI (fully async)
- **Database**: PostgreSQL with SQLAlchemy 2.0
- **Validation**: Pydantic 2
- **Testing**: pytest + testcontainers
- **Package Manager**: uv
- **Migrations**: Atlas
- **Code Quality**: ruff + pre-commit + gitleaks

### Frontend Stack (Future)
- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript
- **UI Library**: ShadCN (Radix UI + Tailwind CSS)
- **State Management**: TBD
- **API Client**: TBD

### Architecture Principles
- Functional cohesion (organize by domain)
- Repository + Service layer patterns
- Async operations throughout
- Transaction isolation in tests
- RESTful API design
- JWT authentication

## Constraints
- Mobile-first design (primary use in gym)
- Fast performance (quick logging between sets)
- Simple UI (easy to use during workouts)
- Google login only (no custom auth)
- Must work on phones and tablets

## Success Criteria
1. User can log a complete workout in < 2 minutes
2. Exercise search returns results instantly
3. Previous workout data easily accessible
4. Works smoothly on mobile devices
5. Reliable data persistence

## Out of Scope (v1)
- Workout planning/templates
- Complex analytics
- Social features
- Nutrition tracking
- Cardio tracking details
- Exercise technique guides

## Key Decisions Made
1. **Backend-first**: API stability before UI
2. **Async Python**: Performance at scale
3. **Real database testing**: Catch SQL issues early
4. **Functional cohesion**: Maintainable architecture
5. **Google SSO only**: Simplified auth
6. **One exercise per workout**: Simplified data model

## Implementation Order
1. Backend API implementation
2. Comprehensive testing suite
3. Frontend UI development
4. Integration and deployment
5. User feedback iteration
