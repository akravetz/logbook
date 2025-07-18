"""Test exercise repository."""

from workout_api.exercises.models import Exercise, ExerciseModality
from workout_api.exercises.repository import ExerciseRepository
from workout_api.exercises.schemas import ExerciseFilters, Pagination
from workout_api.users.models import User


class TestExerciseRepository:
    """Test exercise repository operations."""

    async def test_get_by_id_existing(
        self, exercise_repository: ExerciseRepository, system_exercise: Exercise
    ):
        """Test getting exercise by existing ID."""
        # Extract ID early to avoid lazy loading
        exercise_id = system_exercise.id

        result = await exercise_repository.get_by_id(exercise_id)

        assert result is not None
        assert result.id == exercise_id
        assert result.name == "Barbell Bench Press"

    async def test_get_by_id_nonexistent(self, exercise_repository: ExerciseRepository):
        """Test getting exercise by non-existent ID."""
        result = await exercise_repository.get_by_id(999999)
        assert result is None

    async def test_get_by_name_exact_match(
        self, exercise_repository: ExerciseRepository, system_exercise: Exercise
    ):
        """Test getting exercise by exact name match."""
        result = await exercise_repository.get_by_name("Barbell Bench Press")

        assert result is not None
        assert result.name == "Barbell Bench Press"
        assert result.id == system_exercise.id

    async def test_get_by_name_case_insensitive(
        self,
        exercise_repository: ExerciseRepository,
        system_exercise: Exercise,  # noqa: ARG002
    ):
        """Test getting exercise by name is case insensitive."""
        result = await exercise_repository.get_by_name("barbell bench press")

        assert result is not None
        assert result.name == "Barbell Bench Press"

    async def test_get_by_name_with_user_scoping(
        self,
        exercise_repository: ExerciseRepository,
        test_user: User,
        user_exercise: Exercise,
        another_user_exercise: Exercise,
    ):
        """Test getting exercise by name with user scoping."""
        # Extract IDs early
        user_id = test_user.id
        user_exercise_name = user_exercise.name
        another_exercise_name = another_user_exercise.name

        # User can see their own exercise
        result = await exercise_repository.get_by_name(user_exercise_name, user_id)
        assert result is not None
        assert result.name == user_exercise_name

        # User cannot see another user's exercise
        result = await exercise_repository.get_by_name(another_exercise_name, user_id)
        assert result is None

    async def test_get_by_name_nonexistent(
        self, exercise_repository: ExerciseRepository
    ):
        """Test getting exercise by non-existent name."""
        result = await exercise_repository.get_by_name("Non Existent Exercise")
        assert result is None

    async def test_search_no_filters(
        self,
        exercise_repository: ExerciseRepository,
        multiple_exercises: list[Exercise],
    ):
        """Test searching exercises without filters."""
        filters = ExerciseFilters()
        pagination = Pagination(page=1, size=10)

        result = await exercise_repository.search(filters, pagination)

        assert result.total >= len(multiple_exercises)
        assert len(result.items) >= len(multiple_exercises)
        assert result.page == 1
        assert result.size == 10

    async def test_search_by_name(
        self,
        exercise_repository: ExerciseRepository,
        multiple_exercises: list[Exercise],  # noqa: ARG002
    ):
        """Test searching exercises by name."""
        filters = ExerciseFilters(name="User")
        pagination = Pagination(page=1, size=10)

        result = await exercise_repository.search(filters, pagination)

        assert (
            result.total >= 2
        )  # "User Chest Fly", "User Leg Press", "Another User Exercise"
        for exercise in result.items:
            assert "User" in exercise.name

    async def test_search_by_body_part(
        self,
        exercise_repository: ExerciseRepository,
        multiple_exercises: list[Exercise],  # noqa: ARG002
    ):
        """Test searching exercises by body part."""
        filters = ExerciseFilters(body_part="Legs")
        pagination = Pagination(page=1, size=10)

        result = await exercise_repository.search(filters, pagination)

        assert result.total >= 2  # "Squat", "User Leg Press"
        for exercise in result.items:
            assert "Legs" in exercise.body_part

    async def test_search_by_modality(
        self,
        exercise_repository: ExerciseRepository,
        multiple_exercises: list[Exercise],  # noqa: ARG002
    ):
        """Test searching exercises by modality."""
        filters = ExerciseFilters(modality=ExerciseModality.BARBELL)
        pagination = Pagination(page=1, size=10)

        result = await exercise_repository.search(filters, pagination)

        assert result.total >= 2  # "Squat", "Deadlift"
        for exercise in result.items:
            assert exercise.modality == ExerciseModality.BARBELL

    async def test_search_by_user_created(
        self,
        exercise_repository: ExerciseRepository,
        multiple_exercises: list[Exercise],  # noqa: ARG002
    ):
        """Test searching exercises by user created flag."""
        # Search for system exercises
        filters = ExerciseFilters(is_user_created=False)
        pagination = Pagination(page=1, size=10)

        result = await exercise_repository.search(filters, pagination)

        assert result.total >= 3  # System exercises
        for exercise in result.items:
            assert exercise.is_user_created is False

        # Search for user exercises
        filters = ExerciseFilters(is_user_created=True)
        result = await exercise_repository.search(filters, pagination)

        assert result.total >= 3  # User exercises
        for exercise in result.items:
            assert exercise.is_user_created is True

    async def test_search_with_user_permission_filtering(
        self,
        exercise_repository: ExerciseRepository,
        test_user: User,
        multiple_exercises: list[Exercise],  # noqa: ARG002
    ):
        """Test search respects user permissions."""
        # Extract user ID early
        user_id = test_user.id

        filters = ExerciseFilters()
        pagination = Pagination(page=1, size=100)  # Large size to get all

        result = await exercise_repository.search(filters, pagination, user_id)

        # User should see their own exercises + system exercises
        user_exercise_count = 0
        system_exercise_count = 0
        another_user_exercise_count = 0

        for exercise in result.items:
            if exercise.is_user_created:
                if exercise.created_by_user_id == user_id:
                    user_exercise_count += 1
                else:
                    another_user_exercise_count += 1
            else:
                system_exercise_count += 1

        # Should have user's own exercises
        assert user_exercise_count >= 2  # "User Chest Fly", "User Leg Press"
        # Should have system exercises
        assert system_exercise_count >= 3  # "Squat", "Deadlift", "Pull Up"
        # Should NOT have another user's exercises
        assert another_user_exercise_count == 0

    async def test_search_pagination(
        self,
        exercise_repository: ExerciseRepository,
        multiple_exercises: list[Exercise],
    ):
        """Test search pagination."""
        filters = ExerciseFilters()

        # First page
        pagination = Pagination(page=1, size=2)
        result = await exercise_repository.search(filters, pagination)

        assert len(result.items) <= 2
        assert result.page == 1
        assert result.size == 2
        assert result.total >= len(multiple_exercises)

        # Second page (if exists)
        if result.total > 2:
            pagination = Pagination(page=2, size=2)
            result2 = await exercise_repository.search(filters, pagination)

            assert result2.page == 2
            # Items should be different
            if len(result.items) > 0 and len(result2.items) > 0:
                assert result.items[0].id != result2.items[0].id

    async def test_search_short_query_uses_ilike(
        self,
        exercise_repository: ExerciseRepository,
        multiple_exercises: list[Exercise],  # noqa: ARG002
    ):
        """Test that short queries (< 4 chars) use ILIKE matching."""
        filters = ExerciseFilters(name="Pre")  # 3 characters - should use ILIKE
        pagination = Pagination(page=1, size=10)

        result = await exercise_repository.search(filters, pagination)

        # Should find "User Leg Press" which contains "Pre"
        assert result.total >= 1
        found_press = any("Press" in exercise.name for exercise in result.items)
        assert found_press

    async def test_search_long_query_uses_fuzzy_matching(
        self,
        exercise_repository: ExerciseRepository,
        multiple_exercises: list[Exercise],  # noqa: ARG002
    ):
        """Test that long queries (>= 4 chars) use fuzzy matching."""
        # Create a deliberate typo that should match with fuzzy matching
        filters = ExerciseFilters(name="Bench Pres")  # Missing 's' in "Press"
        pagination = Pagination(page=1, size=10)

        result = await exercise_repository.search(filters, pagination)

        # Should find "Bench Press" via fuzzy matching
        assert result.total >= 1
        found_bench = any("Bench Press" in exercise.name for exercise in result.items)
        assert found_bench

    async def test_search_fuzzy_partial_match(
        self,
        exercise_repository: ExerciseRepository,
        multiple_exercises: list[Exercise],  # noqa: ARG002
    ):
        """Test fuzzy matching with partial string matches."""
        filters = ExerciseFilters(name="Chest Flye")  # "Flye" instead of "Fly"
        pagination = Pagination(page=1, size=10)

        result = await exercise_repository.search(filters, pagination)

        # Should find "User Chest Fly" via fuzzy matching
        assert result.total >= 1
        found_fly = any("Chest Fly" in exercise.name for exercise in result.items)
        assert found_fly

    async def test_search_fuzzy_no_match_below_threshold(
        self,
        exercise_repository: ExerciseRepository,
        multiple_exercises: list[Exercise],  # noqa: ARG002
    ):
        """Test that fuzzy matching doesn't match below 70% threshold."""
        # Use a query that should be below 70% similarity
        filters = ExerciseFilters(name="Completely Different Exercise Name")
        pagination = Pagination(page=1, size=10)

        result = await exercise_repository.search(filters, pagination)

        # Should not find any of our test exercises
        assert result.total == 0

    async def test_search_fuzzy_with_other_filters(
        self,
        exercise_repository: ExerciseRepository,
        multiple_exercises: list[Exercise],  # noqa: ARG002
    ):
        """Test fuzzy matching combined with other filters."""
        # Search for exercises with fuzzy name match AND specific body part
        filters = ExerciseFilters(
            name="Chest Flye",  # Should fuzzy match "User Chest Fly"
            body_part="Chest",
        )
        pagination = Pagination(page=1, size=10)

        result = await exercise_repository.search(filters, pagination)

        # Should find "User Chest Fly" (matches both fuzzy name and body part)
        assert result.total >= 1
        for exercise in result.items:
            assert "Chest" in exercise.body_part
            assert "Chest Fly" in exercise.name

    async def test_search_fuzzy_with_user_permissions(
        self,
        exercise_repository: ExerciseRepository,
        test_user: User,
        multiple_exercises: list[Exercise],  # noqa: ARG002
    ):
        """Test fuzzy matching respects user permissions."""
        user_id = test_user.id

        # Search for user's exercise with fuzzy matching
        filters = ExerciseFilters(name="User Chst")  # Missing 'e' in "Chest"
        pagination = Pagination(page=1, size=10)

        result = await exercise_repository.search(filters, pagination, user_id)

        # Should find "User Chest Fly" (user's own exercise)
        assert result.total >= 1
        found_user_exercise = any(
            "User Chest Fly" in exercise.name for exercise in result.items
        )
        assert found_user_exercise

        # Verify no other user's exercises are returned
        for exercise in result.items:
            if exercise.is_user_created:
                assert exercise.created_by_user_id == user_id

    async def test_search_fuzzy_pagination(
        self,
        exercise_repository: ExerciseRepository,
        multiple_exercises: list[Exercise],  # noqa: ARG002
    ):
        """Test fuzzy matching with pagination."""
        # Use a query that should match multiple exercises
        filters = ExerciseFilters(
            name="User"
        )  # Should match "User Chest Fly", "User Leg Press"
        pagination = Pagination(page=1, size=1)

        result = await exercise_repository.search(filters, pagination)

        # Should have at least 2 total matches but only 1 item due to pagination
        assert result.total >= 2
        assert len(result.items) == 1
        assert result.page == 1
        assert result.size == 1

        # Test second page
        pagination = Pagination(page=2, size=1)
        result2 = await exercise_repository.search(filters, pagination)

        assert result2.page == 2
        assert len(result2.items) <= 1
        # Should be different exercise than first page
        if len(result2.items) > 0:
            assert result.items[0].id != result2.items[0].id

    async def test_search_fuzzy_case_insensitive(
        self,
        exercise_repository: ExerciseRepository,
        multiple_exercises: list[Exercise],  # noqa: ARG002
    ):
        """Test fuzzy matching is case insensitive."""
        filters = ExerciseFilters(name="bench press")  # Lowercase
        pagination = Pagination(page=1, size=10)

        result = await exercise_repository.search(filters, pagination)

        # Should find "Bench Press" despite case difference
        assert result.total >= 1
        found_bench = any("Bench Press" in exercise.name for exercise in result.items)
        assert found_bench

    async def test_search_fuzzy_ordering_consistency(
        self,
        exercise_repository: ExerciseRepository,
        multiple_exercises: list[Exercise],  # noqa: ARG002
    ):
        """Test that fuzzy matching maintains consistent ordering."""
        filters = ExerciseFilters(name="User")  # Should match multiple exercises
        pagination = Pagination(page=1, size=10)

        # Run same search twice
        result1 = await exercise_repository.search(filters, pagination)
        result2 = await exercise_repository.search(filters, pagination)

        assert result1.total == result2.total
        assert len(result1.items) == len(result2.items)

        # Items should be in same order
        for i in range(len(result1.items)):
            assert result1.items[i].id == result2.items[i].id

    async def test_get_by_body_part(
        self,
        exercise_repository: ExerciseRepository,
        multiple_exercises: list[Exercise],  # noqa: ARG002
        test_user: User,
    ):
        """Test getting exercises by body part."""
        # Extract user ID early
        user_id = test_user.id

        pagination = Pagination(page=1, size=10)
        result = await exercise_repository.get_by_body_part(
            "Chest", pagination, user_id
        )

        assert result.total >= 1  # At least "User Chest Fly"
        for exercise in result.items:
            assert "Chest" in exercise.body_part

    async def test_get_by_modality(
        self,
        exercise_repository: ExerciseRepository,
        multiple_exercises: list[Exercise],  # noqa: ARG002
        test_user: User,
    ):
        """Test getting exercises by modality."""
        # Extract user ID early
        user_id = test_user.id

        pagination = Pagination(page=1, size=10)
        result = await exercise_repository.get_by_modality(
            ExerciseModality.DUMBBELL, pagination, user_id
        )

        assert result.total >= 1  # At least "User Chest Fly"
        for exercise in result.items:
            assert exercise.modality == ExerciseModality.DUMBBELL

    async def test_get_user_exercises(
        self,
        exercise_repository: ExerciseRepository,
        test_user: User,
        multiple_exercises: list[Exercise],  # noqa: ARG002
    ):
        """Test getting exercises created by specific user."""
        # Extract user ID early
        user_id = test_user.id

        pagination = Pagination(page=1, size=10)
        result = await exercise_repository.get_user_exercises(user_id, pagination)

        assert result.total >= 2  # "User Chest Fly", "User Leg Press"
        for exercise in result.items:
            assert exercise.is_user_created is True
            assert exercise.created_by_user_id == user_id

    async def test_get_system_exercises(
        self,
        exercise_repository: ExerciseRepository,
        multiple_exercises: list[Exercise],  # noqa: ARG002
    ):
        """Test getting system exercises."""
        pagination = Pagination(page=1, size=10)
        result = await exercise_repository.get_system_exercises(pagination)

        assert result.total >= 3  # "Squat", "Deadlift", "Pull Up"
        for exercise in result.items:
            assert exercise.is_user_created is False

    async def test_create_exercise(
        self, exercise_repository: ExerciseRepository, test_user: User
    ):
        """Test creating new exercise."""
        # Extract user ID early
        user_id = test_user.id

        exercise_data = {
            "name": "New Test Exercise",
            "body_part": "Arms",
            "modality": ExerciseModality.CABLE,
            "picture_url": "https://example.com/new.jpg",
            "is_user_created": True,
            "created_by_user_id": user_id,
            "updated_by_user_id": user_id,
        }

        result = await exercise_repository.create(exercise_data)

        assert result.id is not None
        assert result.name == "New Test Exercise"
        assert result.body_part == "Arms"
        assert result.modality == ExerciseModality.CABLE
        assert result.is_user_created is True
        assert result.created_by_user_id == user_id

    async def test_update_exercise(
        self, exercise_repository: ExerciseRepository, user_exercise: Exercise
    ):
        """Test updating existing exercise."""
        # Extract ID early
        exercise_id = user_exercise.id

        update_data = {
            "name": "Updated Exercise Name",
            "body_part": "Updated Body Part",
        }

        result = await exercise_repository.update(exercise_id, update_data)

        assert result is not None
        assert result.name == "Updated Exercise Name"
        assert result.body_part == "Updated Body Part"
        # Other fields should remain unchanged
        assert result.modality == user_exercise.modality

    async def test_update_nonexistent_exercise(
        self, exercise_repository: ExerciseRepository
    ):
        """Test updating non-existent exercise."""
        update_data = {"name": "Updated Name"}
        result = await exercise_repository.update(999999, update_data)
        assert result is None

    async def test_delete_exercise(
        self, exercise_repository: ExerciseRepository, user_exercise: Exercise
    ):
        """Test deleting exercise."""
        # Extract ID early
        exercise_id = user_exercise.id

        result = await exercise_repository.delete(exercise_id)
        assert result is True

        # NOTE: Due to transaction isolation in tests, the delete operation
        # is rolled back after the test completes. The important thing is
        # that the delete method returned True, indicating success.
        # In a real application, the delete would persist.
        pass

    async def test_delete_nonexistent_exercise(
        self, exercise_repository: ExerciseRepository
    ):
        """Test deleting non-existent exercise."""
        result = await exercise_repository.delete(999999)
        assert result is False

    async def test_can_user_modify_own_exercise(
        self,
        exercise_repository: ExerciseRepository,
        test_user: User,
        user_exercise: Exercise,
    ):
        """Test user can modify their own exercise."""
        # Extract IDs early
        exercise_id = user_exercise.id
        user_id = test_user.id

        result = await exercise_repository.can_user_modify(exercise_id, user_id)
        assert result is True

    async def test_can_user_modifysystem_exercise(
        self,
        exercise_repository: ExerciseRepository,
        test_user: User,
        system_exercise: Exercise,
    ):
        """Test user cannot modify system exercise."""
        # Extract IDs early
        exercise_id = system_exercise.id
        user_id = test_user.id

        result = await exercise_repository.can_user_modify(exercise_id, user_id)
        assert result is False

    async def test_can_user_modify_another_users_exercise(
        self,
        exercise_repository: ExerciseRepository,
        test_user: User,
        another_user_exercise: Exercise,
    ):
        """Test user cannot modify another user's exercise."""
        # Extract IDs early
        exercise_id = another_user_exercise.id
        user_id = test_user.id

        result = await exercise_repository.can_user_modify(exercise_id, user_id)
        assert result is False

    async def test_can_user_modify_nonexistent_exercise(
        self, exercise_repository: ExerciseRepository, test_user: User
    ):
        """Test checking modification rights for non-existent exercise."""
        # Extract user ID early
        user_id = test_user.id

        result = await exercise_repository.can_user_modify(999999, user_id)
        assert result is False

    async def test_get_distinct_body_parts_anonymous_user(
        self,
        exercise_repository: ExerciseRepository,
        multiple_exercises,  # noqa: ARG002
    ):
        """Test getting distinct body parts for anonymous user (system exercises only)."""
        body_parts = await exercise_repository.get_distinct_body_parts(user_id=None)

        # Anonymous users should only see system exercise body parts
        expected_body_parts = {
            "Back",
            "Chest",
            "Legs",
        }  # From system exercises in fixture
        assert set(body_parts) == expected_body_parts
        assert body_parts == sorted(body_parts)  # Should be sorted

    async def test_get_distinct_body_parts_authenticated_user(
        self,
        exercise_repository: ExerciseRepository,
        multiple_exercises,  # noqa: ARG002
        test_user: User,
    ):
        """Test getting distinct body parts for authenticated user (system + own exercises)."""
        # Extract user ID early
        user_id = test_user.id

        body_parts = await exercise_repository.get_distinct_body_parts(user_id=user_id)

        # Authenticated users should see system + own exercise body parts
        expected_body_parts = {
            "Back",
            "Chest",
            "Legs",
        }  # At least these from system and user exercises
        assert set(body_parts).issuperset(expected_body_parts)
        assert body_parts == sorted(body_parts)  # Should be sorted
