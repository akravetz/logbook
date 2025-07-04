"""Registry for managing available database seeders."""

import logging

from .base import BaseSeeder

logger = logging.getLogger(__name__)


class SeederRegistry:
    """Registry for managing available database seeders."""

    _seeders: dict[str, type[BaseSeeder]] = {}

    @classmethod
    def register(cls, name: str, seeder_class: type[BaseSeeder]) -> None:
        """Register a seeder class.

        Args:
            name: Unique name for the seeder
            seeder_class: Seeder class to register
        """
        if name in cls._seeders:
            logger.warning(f"Seeder '{name}' is already registered, overwriting")

        cls._seeders[name] = seeder_class
        logger.debug(f"Registered seeder: {name}")

    @classmethod
    def get_seeder(cls, name: str) -> type[BaseSeeder] | None:
        """Get a seeder class by name.

        Args:
            name: Name of the seeder

        Returns:
            Seeder class or None if not found
        """
        return cls._seeders.get(name)

    @classmethod
    def get_all_seeders(cls) -> dict[str, type[BaseSeeder]]:
        """Get all registered seeders.

        Returns:
            Dictionary of seeder name to seeder class
        """
        return cls._seeders.copy()

    @classmethod
    def list_seeder_names(cls) -> list[str]:
        """Get list of all registered seeder names.

        Returns:
            List of seeder names
        """
        return list(cls._seeders.keys())

    @classmethod
    def is_registered(cls, name: str) -> bool:
        """Check if a seeder is registered.

        Args:
            name: Name of the seeder

        Returns:
            True if seeder is registered
        """
        return name in cls._seeders


def register_seeder(name: str):
    """Decorator to register a seeder class.

    Args:
        name: Unique name for the seeder
    """

    def decorator(seeder_class: type[BaseSeeder]):
        SeederRegistry.register(name, seeder_class)
        return seeder_class

    return decorator
