"""Load SQLAlchemy models for Atlas migration generation."""

# Import all models to ensure they're registered with the Base metadata
from atlas_provider_sqlalchemy.ddl import print_ddl

from workout_api.exercises.models import Exercise
from workout_api.users.models import User
from workout_api.workouts.models import ExerciseExecution, Set, Workout

# Generate DDL for PostgreSQL with all models
print_ddl("postgresql", [User, Exercise, Workout, ExerciseExecution, Set])
