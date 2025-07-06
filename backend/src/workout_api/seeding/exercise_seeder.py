"""Exercise seeder for loading system exercises from CSV."""

import csv
import logging
from pathlib import Path
from typing import Any

from sqlalchemy import insert, select, text

from ..exercises.models import Exercise, ExerciseModality
from ..exercises.repository import ExerciseRepository
from .base import BaseSeeder, CleanResult, SeedResult
from .seeder_registry import register_seeder

logger = logging.getLogger(__name__)


@register_seeder("exercises")
class ExerciseSeeder(BaseSeeder):
    """Seeder for loading system exercises from CSV file."""

    def __init__(self, session, dry_run: bool = False, force: bool = False):
        """Initialize the exercise seeder."""
        super().__init__(session, dry_run, force)
        self.repository = ExerciseRepository(session)

    def get_name(self) -> str:
        """Get the human-readable name of this seeder."""
        return "Exercise Seeder"

    async def should_skip_existing(self) -> bool:
        """Exercise seeder skips existing items by default."""
        return True

    def get_managed_tables(self) -> list[str]:
        """Get list of table names this seeder manages."""
        return ["exercises"]

    async def clean(self) -> CleanResult:
        """Clean (truncate) the exercises table.

        Returns:
            CleanResult containing operation results
        """
        result = CleanResult(tables_cleaned=[], rows_deleted=0)

        try:
            # First, get the count of rows to be deleted
            count_result = await self.session.execute(
                text("SELECT COUNT(*) FROM exercises WHERE is_user_created = FALSE")
            )
            rows_count = count_result.scalar() or 0

            if self.dry_run:
                self.logger.info(
                    f"[DRY RUN] Would delete {rows_count} system exercises"
                )
                result.tables_cleaned = ["exercises"]
                result.rows_deleted = rows_count
                return result

            # Delete only system exercises (not user-created ones)
            delete_result = await self.session.execute(
                text("DELETE FROM exercises WHERE is_user_created = FALSE")
            )

            actual_deleted = delete_result.rowcount or 0

            self.logger.info(f"Deleted {actual_deleted} system exercises")

            result.tables_cleaned = ["exercises"]
            result.rows_deleted = actual_deleted

            return result

        except Exception as e:
            error_msg = f"Failed to clean exercises table: {e}"
            self.logger.error(error_msg)
            result.add_error(error_msg)
            return result

    def _get_csv_path(self, csv_file_path: str | None = None) -> Path:
        """Get the path to the exercises CSV file."""
        if csv_file_path:
            return Path(csv_file_path)

        # Default to exercises.csv in scripts/seeds directory
        script_dir = Path(__file__).parent.parent.parent.parent / "scripts" / "seeds"
        return script_dir / "exercises.csv"

    def _parse_csv_row(
        self, row: dict[str, str], row_num: int
    ) -> dict[str, Any] | None:
        """Parse a CSV row into exercise data.

        Args:
            row: CSV row as dictionary
            row_num: Row number for error reporting

        Returns:
            Exercise data dictionary or None if invalid
        """
        try:
            # Expected CSV format: name, body_part, modality
            name = row.get("name", "").strip()
            body_part = row.get("body_part", "").strip()
            modality_str = row.get("modality", "").strip().upper()

            if not name or not body_part or not modality_str:
                self.logger.error(
                    f"Row {row_num}: Missing required fields (name, body_part, modality)"
                )
                return None

            # Validate modality
            try:
                modality = ExerciseModality(modality_str)
            except ValueError:
                self.logger.error(
                    f"Row {row_num}: Invalid modality '{modality_str}'. Must be one of: {[m.value for m in ExerciseModality]}"
                )
                return None

            return {
                "name": name,
                "body_part": body_part.lower(),
                "modality": modality,
                "picture_url": None,
                "created_by_user_id": None,
                "updated_by_user_id": None,
                "is_user_created": False,  # System exercise
            }

        except Exception as e:
            self.logger.error(f"Row {row_num}: Error parsing row: {e}")
            return None

    def _read_csv_file(self, csv_path: Path) -> list[dict[str, Any]]:
        """Read and parse the CSV file.

        Args:
            csv_path: Path to the CSV file

        Returns:
            List of exercise data dictionaries

        Raises:
            FileNotFoundError: If CSV file doesn't exist
            ValueError: If CSV headers don't match expected format
        """
        if not csv_path.exists():
            raise FileNotFoundError(f"CSV file not found: {csv_path}")

        exercises = []
        expected_headers = ["name", "body_part", "modality"]

        with open(csv_path, encoding="utf-8") as file:
            reader = csv.DictReader(file)

            # Validate headers
            if not reader.fieldnames:
                raise ValueError("CSV file must have headers")

            # Check that headers match exactly what we expect
            actual_headers = [header.strip() for header in reader.fieldnames]
            if actual_headers != expected_headers:
                raise ValueError(
                    f"CSV headers must be exactly {expected_headers}, "
                    f"but found {actual_headers}"
                )

            self.logger.info(f"Validated CSV headers: {actual_headers}")

            for row_num, row in enumerate(
                reader, start=2
            ):  # Start at 2 since row 1 is headers
                exercise_data = self._parse_csv_row(row, row_num)
                if exercise_data:
                    exercises.append(exercise_data)

        self.logger.info(f"Successfully parsed {len(exercises)} exercises from CSV")
        return exercises

    async def _bulk_insert_exercises(self, exercises_data: list[dict[str, Any]]) -> int:
        """Insert exercises using bulk operation.

        Args:
            exercises_data: List of exercise dictionaries to insert

        Returns:
            Number of exercises inserted
        """
        if not exercises_data:
            return 0

        if self.dry_run:
            self.logger.info(
                f"[DRY RUN] Would bulk insert {len(exercises_data)} exercises"
            )
            return len(exercises_data)

        stmt = insert(Exercise).values(exercises_data)
        await self.session.execute(stmt)
        self.logger.debug(f"Bulk inserted {len(exercises_data)} exercises")
        return len(exercises_data)

    async def _process_exercises_in_batches(
        self, exercises_data: list[dict[str, Any]], batch_size: int = 100
    ) -> tuple[int, int]:
        """Process exercises in batches for memory efficiency.

        Args:
            exercises_data: List of exercise dictionaries to process
            batch_size: Number of exercises to process per batch

        Returns:
            Tuple of (created_count, skipped_count)
        """
        if not exercises_data:
            return 0, 0

        # Get existing exercise names once
        existing_names = await self._get_existing_exercise_names()
        self.logger.info(f"Found {len(existing_names)} existing exercises")

        # Filter out existing exercises unless in force mode
        new_exercises = []
        skipped_count = 0

        for exercise_data in exercises_data:
            exercise_name = exercise_data["name"].lower()
            if not self.force and exercise_name in existing_names:
                self.logger.debug(
                    f"Skipping existing exercise: {exercise_data['name']}"
                )
                skipped_count += 1
                continue
            new_exercises.append(exercise_data)

        if not new_exercises:
            self.logger.info("No new exercises to insert")
            return 0, skipped_count

        self.logger.info(
            f"Processing {len(new_exercises)} new exercises in batches of {batch_size}"
        )

        # Process in batches
        created_count = 0
        for i in range(0, len(new_exercises), batch_size):
            batch = new_exercises[i : i + batch_size]
            batch_created = await self._bulk_insert_exercises(batch)
            created_count += batch_created

            # Log progress
            processed = min(i + batch_size, len(new_exercises))
            await self.log_progress(processed, len(new_exercises), "exercise")

        return created_count, skipped_count

    async def _get_existing_exercise_names(self) -> set[str]:
        """Get all existing system exercise names in a single query.

        Returns:
            Set of existing exercise names (lowercase for case-insensitive comparison)
        """
        stmt = select(Exercise.name).where(~Exercise.is_user_created)
        result = await self.session.execute(stmt)
        return {name.lower() for name in result.scalars().all()}

    async def seed(self, csv_file_path: str | None = None) -> SeedResult:
        """Seed exercises from CSV file.

        Args:
            csv_file_path: Optional path to CSV file (defaults to scripts/seeds/exercises.csv)
            **kwargs: Additional arguments (ignored)

        Returns:
            SeedResult with operation results
        """
        result = self.create_result()

        try:
            # Read CSV file
            csv_path = self._get_csv_path(csv_file_path)
            self.logger.info(f"Reading exercises from: {csv_path}")

            exercises_data = self._read_csv_file(csv_path)
            result.total_items = len(exercises_data)

            if not exercises_data:
                self.logger.warning("No exercises found in CSV file")
                return result

            self.logger.info(f"Processing {len(exercises_data)} exercises...")

            # Process exercises in batches for optimal performance
            try:
                created_count, skipped_count = await self._process_exercises_in_batches(
                    exercises_data
                )

                result.created_items = created_count
                result.skipped_items = skipped_count

                # Final progress log
                await self.log_progress(
                    result.total_items, result.total_items, "exercise"
                )

            except Exception as e:
                error_msg = f"Failed to process exercises in batches: {e}"
                self.logger.error(error_msg)
                result.add_error(error_msg)

            # Commit transaction if not dry run and no errors
            if not self.dry_run and result.success:
                await self.session.commit()
                self.logger.info("Successfully committed exercise seeding transaction")
            elif not self.dry_run:
                await self.session.rollback()
                self.logger.error("Rolled back transaction due to errors")

        except Exception as e:
            error_msg = f"Critical error during exercise seeding: {e}"
            self.logger.error(error_msg)
            result.add_error(error_msg)

            if not self.dry_run:
                await self.session.rollback()

        return result
