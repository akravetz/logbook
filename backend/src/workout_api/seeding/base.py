"""Base seeder class and common functionality."""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class SeedResult:
    """Result of a seeding operation."""

    seeder_name: str
    total_items: int
    created_items: int
    skipped_items: int
    errors: list[str]
    success: bool

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
        return (
            f"{status} {self.seeder_name}: "
            f"{self.created_items} created, "
            f"{self.updated_items} updated, "
            f"{self.skipped_items} skipped, "
            f"{len(self.errors)} errors"
        )


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
