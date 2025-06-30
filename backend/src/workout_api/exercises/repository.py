"""Exercise repository for database operations."""

import logging
from typing import TYPE_CHECKING

from rapidfuzz import fuzz, process
from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import Exercise, ExerciseModality
from .schemas import ExerciseFilters, Pagination

if TYPE_CHECKING:
    from .schemas import Page

logger = logging.getLogger(__name__)


class ExerciseRepository:
    """Repository for exercise database operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, exercise_id: int) -> Exercise | None:
        """Get exercise by ID."""
        result = await self.session.get(Exercise, exercise_id)
        return result

    async def get_by_name(
        self, name: str, user_id: int | None = None
    ) -> Exercise | None:
        """Get exercise by name, optionally scoped to user's exercises + system exercises."""
        stmt = select(Exercise).where(Exercise.name.ilike(name.strip()))

        if user_id is not None:
            # User can see their own exercises + system exercises
            stmt = stmt.where(
                or_(
                    Exercise.created_by_user_id == user_id,
                    ~Exercise.is_user_created,  # System exercises
                )
            )

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    def _build_base_conditions(self, filters: ExerciseFilters) -> list:
        """Build all search conditions except name filtering."""
        conditions = []

        # Apply non-name filters
        if filters.body_part:
            conditions.append(
                Exercise.body_part.ilike(f"%{filters.body_part.strip()}%")
            )

        if filters.modality:
            conditions.append(Exercise.modality == filters.modality)

        if filters.is_user_created is not None:
            conditions.append(Exercise.is_user_created == filters.is_user_created)

        if filters.created_by_user_id:
            conditions.append(Exercise.created_by_user_id == filters.created_by_user_id)

        return conditions

    def _build_permission_filter(self, user_id: int | None):
        """Build permission filtering clause."""
        if user_id is not None:
            return or_(
                Exercise.created_by_user_id == user_id,
                ~Exercise.is_user_created,  # System exercises
            )
        return None

    async def _search_without_name_filter(
        self, base_conditions: list, pagination: Pagination, user_id: int | None = None
    ) -> "Page[Exercise]":
        """Search exercises without name filtering (original logic)."""
        stmt = select(Exercise)
        count_stmt = select(func.count(Exercise.id))

        # Apply permission filtering
        permission_filter = self._build_permission_filter(user_id)
        if permission_filter is not None:
            stmt = stmt.where(permission_filter)
            count_stmt = count_stmt.where(permission_filter)

        # Apply other conditions
        if base_conditions:
            filter_clause = and_(*base_conditions)
            stmt = stmt.where(filter_clause)
            count_stmt = count_stmt.where(filter_clause)

        # Apply pagination and ordering
        stmt = (
            stmt.order_by(Exercise.name)
            .offset(pagination.offset)
            .limit(pagination.size)
        )

        # Execute queries
        result = await self.session.execute(stmt)
        exercises = result.scalars().all()

        count_result = await self.session.execute(count_stmt)
        total = count_result.scalar()

        from .schemas import Page

        return Page.create(
            items=list(exercises),
            total=total,
            page=pagination.page,
            size=pagination.size,
        )

    async def _search_with_simple_name_filter(
        self,
        base_conditions: list,
        name_query: str,
        pagination: Pagination,
        user_id: int | None = None,
    ) -> "Page[Exercise]":
        """Search exercises with simple ILIKE name filtering for short queries."""
        conditions = base_conditions.copy()
        conditions.append(Exercise.name.ilike(f"%{name_query}%"))

        return await self._search_without_name_filter(conditions, pagination, user_id)

    async def _search_with_fuzzy_name_filter(
        self,
        base_conditions: list,
        name_query: str,
        pagination: Pagination,
        user_id: int | None = None,
    ) -> "Page[Exercise]":
        """Search exercises with fuzzy name matching for longer queries."""
        # Step 1: Get all exercises matching non-name criteria
        stmt = select(Exercise)

        # Apply permission filtering
        permission_filter = self._build_permission_filter(user_id)
        if permission_filter is not None:
            stmt = stmt.where(permission_filter)

        # Apply non-name conditions
        if base_conditions:
            filter_clause = and_(*base_conditions)
            stmt = stmt.where(filter_clause)

        # Get all candidates (no pagination yet)
        stmt = stmt.order_by(Exercise.name)
        result = await self.session.execute(stmt)
        all_candidates = result.scalars().all()

        # Step 2: Apply fuzzy filtering using rapidfuzz.process for efficiency
        if not all_candidates:
            from .schemas import Page

            return Page.create(
                items=[],
                total=0,
                page=pagination.page,
                size=pagination.size,
            )

        # Create a mapping of exercise names to exercise objects
        exercise_map = {exercise.name: exercise for exercise in all_candidates}
        exercise_names = list(exercise_map.keys())

        # Use rapidfuzz.process.extract for efficient batch fuzzy matching
        fuzzy_results = process.extract(
            name_query,
            exercise_names,
            scorer=fuzz.partial_ratio,
            score_cutoff=70,
            limit=None,  # Get all matches above threshold
        )

        # Convert back to exercise objects, maintaining score order
        fuzzy_matches = [exercise_map[name] for name, score, _ in fuzzy_results]

        # Step 3: Apply pagination to fuzzy results
        total = len(fuzzy_matches)
        start_idx = pagination.offset
        end_idx = start_idx + pagination.size
        paginated_exercises = fuzzy_matches[start_idx:end_idx]

        from .schemas import Page

        return Page.create(
            items=paginated_exercises,
            total=total,
            page=pagination.page,
            size=pagination.size,
        )

    async def search(
        self,
        filters: ExerciseFilters,
        pagination: Pagination,
        user_id: int | None = None,
    ) -> "Page[Exercise]":
        """Search exercises with filters and pagination.

        Uses different strategies based on name query length:
        - No name filter: Standard database query
        - Short name queries (< 4 chars): ILIKE database matching
        - Long name queries (>= 4 chars): Fuzzy matching with rapidfuzz
        """
        # Build base conditions (all filters except name)
        base_conditions = self._build_base_conditions(filters)

        # Handle name filtering with different strategies
        if not filters.name:
            # No name filter - use standard logic
            return await self._search_without_name_filter(
                base_conditions, pagination, user_id
            )

        name_query = filters.name.strip()
        if len(name_query) < 4:
            # Short query - use simple ILIKE matching
            return await self._search_with_simple_name_filter(
                base_conditions, name_query, pagination, user_id
            )
        else:
            # Long query - use fuzzy matching
            return await self._search_with_fuzzy_name_filter(
                base_conditions, name_query, pagination, user_id
            )

    async def get_by_body_part(
        self, body_part: str, pagination: Pagination, user_id: int | None = None
    ) -> "Page[Exercise]":
        """Get exercises by body part with pagination."""
        filters = ExerciseFilters(body_part=body_part)
        return await self.search(filters, pagination, user_id)

    async def get_by_modality(
        self,
        modality: ExerciseModality,
        pagination: Pagination,
        user_id: int | None = None,
    ) -> "Page[Exercise]":
        """Get exercises by modality with pagination."""
        filters = ExerciseFilters(modality=modality)
        return await self.search(filters, pagination, user_id)

    async def get_user_exercises(
        self, user_id: int, pagination: Pagination
    ) -> "Page[Exercise]":
        """Get exercises created by a specific user."""
        filters = ExerciseFilters(created_by_user_id=user_id, is_user_created=True)
        return await self.search(filters, pagination, user_id)

    async def get_system_exercises(self, pagination: Pagination) -> "Page[Exercise]":
        """Get system exercises."""
        filters = ExerciseFilters(is_user_created=False)
        return await self.search(filters, pagination)

    async def create(self, exercise_data: dict) -> Exercise:
        """Create a new exercise."""
        exercise = Exercise(**exercise_data)
        self.session.add(exercise)
        await self.session.flush()  # Get the ID without committing
        await self.session.refresh(exercise)
        return exercise

    async def update(self, exercise_id: int, exercise_data: dict) -> Exercise | None:
        """Update an existing exercise."""
        exercise = await self.get_by_id(exercise_id)
        if not exercise:
            return None

        for key, value in exercise_data.items():
            if hasattr(exercise, key):
                setattr(exercise, key, value)

        await self.session.flush()
        await self.session.refresh(exercise)
        return exercise

    async def delete(self, exercise_id: int) -> bool:
        """Hard delete an exercise (for system cleanup only)."""
        exercise = await self.get_by_id(exercise_id)
        if not exercise:
            return False

        await self.session.delete(exercise)
        return True

    async def can_user_modify(self, exercise_id: int, user_id: int) -> bool:
        """Check if user can modify the exercise (only their own exercises)."""
        exercise = await self.get_by_id(exercise_id)
        if not exercise:
            return False

        return exercise.is_user_created and exercise.created_by_user_id == user_id

    async def get_distinct_body_parts(self, user_id: int | None = None) -> list[str]:
        """Get distinct body parts with proper permission filtering."""
        stmt = select(Exercise.body_part).distinct()

        if user_id is not None:
            # User can see their own exercises + system exercises
            permission_filter = or_(
                Exercise.created_by_user_id == user_id,
                ~Exercise.is_user_created,  # System exercises
            )
            stmt = stmt.where(permission_filter)
        else:
            # Anonymous users can only see system exercises
            stmt = stmt.where(~Exercise.is_user_created)

        result = await self.session.execute(stmt)
        body_parts = [
            bp for bp in result.scalars().all() if bp
        ]  # Filter out None/empty
        return sorted(body_parts)
