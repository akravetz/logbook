"""Exercise service for business logic."""

import logging

from sqlalchemy.ext.asyncio import AsyncSession

from ..shared.exceptions import NotFoundError, ValidationError
from .models import ExerciseModality
from .repository import ExerciseRepository
from .schemas import (
    ExerciseCreate,
    ExerciseFilters,
    ExerciseResponse,
    ExerciseUpdate,
    Page,
    Pagination,
)

logger = logging.getLogger(__name__)


class ExerciseService:
    """Service for exercise business logic."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repository = ExerciseRepository(session)

    async def search_exercises(
        self,
        filters: ExerciseFilters,
        pagination: Pagination,
        user_id: int | None = None,
    ) -> Page[ExerciseResponse]:
        """Search exercises with filters and pagination."""
        page = await self.repository.search(filters, pagination, user_id)

        # Convert SQLAlchemy objects to Pydantic models within session context
        exercise_responses = [
            ExerciseResponse.model_validate(exercise) for exercise in page.items
        ]

        return Page.create(
            items=exercise_responses, total=page.total, page=page.page, size=page.size
        )

    async def get_exercise_by_id(
        self, exercise_id: int, user_id: int | None = None
    ) -> ExerciseResponse:
        """Get exercise by ID with permission checking."""
        exercise = await self.repository.get_by_id(exercise_id)
        if not exercise:
            raise NotFoundError(f"Exercise not found with ID: {exercise_id}")

        # Check if user has permission to view this exercise
        if (
            user_id is not None
            and exercise.is_user_created
            and exercise.created_by_user_id != user_id
        ):
            raise NotFoundError(f"Exercise not found with ID: {exercise_id}")

        # Convert to Pydantic model within session context
        return ExerciseResponse.model_validate(exercise)

    async def create_user_exercise(
        self, exercise_data: ExerciseCreate, user_id: int
    ) -> ExerciseResponse:
        """Create a new user exercise with validation."""
        # Trim and validate name
        name = exercise_data.name.strip()
        if not name:
            raise ValidationError("Exercise name cannot be empty")

        # Check for duplicate exercise name for this user
        existing = await self.repository.get_by_name(name, user_id)
        if existing:
            raise ValidationError(f"Exercise with name '{name}' already exists")

        # Prepare exercise data
        create_data = {
            "name": name,
            "body_part": exercise_data.body_part.strip(),
            "modality": exercise_data.modality,
            "picture_url": str(exercise_data.picture_url)
            if exercise_data.picture_url
            else None,
            "created_by_user_id": user_id,
            "updated_by_user_id": user_id,
            "is_user_created": True,
        }

        # Create exercise
        exercise = await self.repository.create(create_data)

        # Convert to Pydantic model within session context
        exercise_response = ExerciseResponse.model_validate(exercise)

        # Commit the transaction
        await self.session.commit()

        return exercise_response

    async def update_user_exercise(
        self, exercise_id: int, exercise_data: ExerciseUpdate, user_id: int
    ) -> ExerciseResponse:
        """Update a user exercise with validation."""
        # Check if exercise exists first
        exercise = await self.repository.get_by_id(exercise_id)
        if not exercise:
            raise NotFoundError(f"Exercise not found with ID: {exercise_id}")

        # Check if user can modify it
        if not await self.repository.can_user_modify(exercise_id, user_id):
            raise ValidationError("You can only modify your own exercises")

        # Prepare update data, excluding None values
        update_data = exercise_data.model_dump(exclude_none=True)

        if not update_data:
            # No data to update, return current exercise
            return await self.get_exercise_by_id(exercise_id, user_id)

        # Validate and trim name if provided
        if "name" in update_data:
            name = update_data["name"].strip()
            if not name:
                raise ValidationError("Exercise name cannot be empty")

            # Check for duplicate name (excluding current exercise)
            existing = await self.repository.get_by_name(name, user_id)
            if existing and existing.id != exercise_id:
                raise ValidationError(f"Exercise '{name}' already exists")

            update_data["name"] = name

        # Trim body_part if provided
        if "body_part" in update_data:
            update_data["body_part"] = update_data["body_part"].strip()

        # Convert picture_url to string if provided
        if "picture_url" in update_data and update_data["picture_url"]:
            update_data["picture_url"] = str(update_data["picture_url"])

        # Add updated_by_user_id
        update_data["updated_by_user_id"] = user_id

        # Update exercise
        updated_exercise = await self.repository.update(exercise_id, update_data)
        if not updated_exercise:
            raise NotFoundError(f"Exercise not found with ID: {exercise_id}")

        # Convert to Pydantic model within session context
        exercise_response = ExerciseResponse.model_validate(updated_exercise)

        # Commit the transaction
        await self.session.commit()

        return exercise_response

    async def delete_user_exercise(self, exercise_id: int, user_id: int) -> bool:
        """Delete a user exercise with permission checking."""
        # Check if exercise exists first
        exercise = await self.repository.get_by_id(exercise_id)
        if not exercise:
            raise NotFoundError(f"Exercise not found with ID: {exercise_id}")

        # Check if user can modify it
        if not await self.repository.can_user_modify(exercise_id, user_id):
            raise ValidationError("You can only delete your own exercises")

        # Delete exercise
        success = await self.repository.delete(exercise_id)
        if success:
            await self.session.commit()

        return success

    async def get_by_body_part(
        self, body_part: str, pagination: Pagination, user_id: int | None = None
    ) -> Page[ExerciseResponse]:
        """Get exercises by body part."""
        filters = ExerciseFilters(body_part=body_part)
        return await self.search_exercises(filters, pagination, user_id)

    async def get_by_modality(
        self, modality: str, pagination: Pagination, user_id: int | None = None
    ) -> Page[ExerciseResponse]:
        """Get exercises by modality."""
        try:
            modality_enum = ExerciseModality(modality.upper())
            filters = ExerciseFilters(modality=modality_enum)
            return await self.search_exercises(filters, pagination, user_id)
        except ValueError as e:
            raise ValidationError(f"Invalid modality: {modality}") from e

    async def get_user_exercises(
        self, user_id: int, pagination: Pagination
    ) -> Page[ExerciseResponse]:
        """Get exercises created by a specific user."""
        page = await self.repository.get_user_exercises(user_id, pagination)

        # Convert SQLAlchemy objects to Pydantic models within session context
        exercise_responses = [
            ExerciseResponse.model_validate(exercise) for exercise in page.items
        ]

        return Page.create(
            items=exercise_responses, total=page.total, page=page.page, size=page.size
        )

    async def get_system_exercises(
        self, pagination: Pagination
    ) -> Page[ExerciseResponse]:
        """Get system exercises."""
        filters = ExerciseFilters(is_user_created=False)
        return await self.search_exercises(filters, pagination)

    # Alias methods for test compatibility
    async def search(
        self,
        filters: ExerciseFilters,
        pagination: Pagination,
        user_id: int | None = None,
    ) -> Page[ExerciseResponse]:
        """Alias for search_exercises."""
        return await self.search_exercises(filters, pagination, user_id)

    async def get_by_id(self, exercise_id: int) -> ExerciseResponse:
        """Alias for get_exercise_by_id."""
        return await self.get_exercise_by_id(exercise_id)

    async def get_by_name(
        self, name: str, user_id: int | None = None
    ) -> ExerciseResponse | None:
        """Get exercise by name."""
        exercise = await self.repository.get_by_name(name, user_id)
        if not exercise:
            return None

        # Convert to Pydantic model within session context
        return ExerciseResponse.model_validate(exercise)

    async def create(
        self, exercise_data: ExerciseCreate, user_id: int
    ) -> ExerciseResponse:
        """Alias for create_user_exercise."""
        return await self.create_user_exercise(exercise_data, user_id)

    async def update(
        self, exercise_id: int, exercise_data: ExerciseUpdate, user_id: int
    ) -> ExerciseResponse:
        """Alias for update_user_exercise."""
        return await self.update_user_exercise(exercise_id, exercise_data, user_id)

    async def delete(self, exercise_id: int, user_id: int) -> bool:
        """Alias for delete_user_exercise."""
        return await self.delete_user_exercise(exercise_id, user_id)

    async def get_available_body_parts(self, user_id: int | None = None) -> list[str]:
        """Get available body parts for exercises user can access."""
        return await self.repository.get_distinct_body_parts(user_id)
