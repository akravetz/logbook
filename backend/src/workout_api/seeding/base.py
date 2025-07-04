"""Base seeder class and common functionality."""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class CleanResult:
    """Result of a table cleaning operation."""

    tables_cleaned: list[str]
    rows_deleted: int
    success: bool = True
    errors: list[str] = field(default_factory=list)

    def add_error(self, error: str) -> None:
        """Add an error to the result."""
        self.errors.append(error)
        self.success = False

    def __str__(self) -> str:
        status = "✅ SUCCESS" if self.success else "❌ FAILED"
        if self.errors:
            return f"{status} Clean: {len(self.errors)} errors"
        return f"{status} Clean: {len(self.tables_cleaned)} tables, {self.rows_deleted} rows deleted"


@dataclass
class SeedResult:
    """Result of a seeding operation."""

    seeder_name: str
    total_items: int
    created_items: int
    skipped_items: int
    errors: list[str]
    success: bool
    clean_result: CleanResult | None = None

    @property
    def updated_items(self) -> int:
        """Calculate updated items (total - created - skipped)."""
        return max(0, self.total_items - self.created_items - self.skipped_items)

    def add_error(self, error: str) -> None:
        """Add an error to the result."""
        self.errors.append(error)
        self.success = False

    def __str__(self) -> str:
        """String representation of the result."""
        status = "✅ SUCCESS" if self.success else "❌ FAILED"

        parts = []
        if self.clean_result:
            parts.append(f"cleaned {self.clean_result.rows_deleted} rows")

        parts.extend(
            [
                f"{self.created_items} created",
                f"{self.updated_items} updated",
                f"{self.skipped_items} skipped",
                f"{len(self.errors)} errors",
            ]
        )

        return f"{status} {self.seeder_name}: {', '.join(parts)}"


class BaseSeeder(ABC):
    """Abstract base class for all database seeders."""

    def __init__(self, session, dry_run: bool = False, force: bool = False):
        """Initialize the seeder.

        Args:
            session: Database session
            dry_run: If True, don't actually write to database
            force: If True, skip existing item checks
        """
        self.session = session
        self.dry_run = dry_run
        self.force = force
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    @abstractmethod
    async def seed(self, **kwargs) -> SeedResult:
        """Perform the seeding operation.

        Returns:
            SeedResult containing operation results
        """
        pass

    @abstractmethod
    def get_name(self) -> str:
        """Get the human-readable name of this seeder."""
        pass

    @abstractmethod
    async def should_skip_existing(self) -> bool:
        """Whether this seeder should skip existing items by default."""
        pass

    @abstractmethod
    async def clean(self) -> CleanResult:
        """Clean (truncate) tables managed by this seeder.

        Returns:
            CleanResult containing operation results
        """
        pass

    @abstractmethod
    def get_managed_tables(self) -> list[str]:
        """Get list of table names this seeder manages.

        Returns:
            List of table names that this seeder is responsible for
        """
        pass

    async def log_progress(
        self, current: int, total: int, item_name: str = "item"
    ) -> None:
        """Log progress during seeding."""
        if total > 0:
            percentage = (current / total) * 100
            self.logger.info(
                f"Progress: {current}/{total} {item_name}s ({percentage:.1f}%)"
            )

    def create_result(
        self,
        total_items: int = 0,
        created_items: int = 0,
        skipped_items: int = 0,
        errors: list[str] | None = None,
    ) -> SeedResult:
        """Create a SeedResult for this seeder."""
        return SeedResult(
            seeder_name=self.get_name(),
            total_items=total_items,
            created_items=created_items,
            skipped_items=skipped_items,
            errors=errors or [],
            success=len(errors or []) == 0,
        )
