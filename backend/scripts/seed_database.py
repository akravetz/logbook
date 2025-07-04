#!/usr/bin/env python3
"""Database seeding CLI script."""

import argparse
import asyncio
import logging
import os
import sys
from dataclasses import dataclass
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from workout_api.core.config import Settings
from workout_api.core.database import DatabaseManager
from workout_api.exercises.models import Exercise  # noqa: F401
from workout_api.seeding import SeederRegistry
from workout_api.seeding.base import SeedResult
from workout_api.seeding.exercise_seeder import (
    ExerciseSeeder,  # noqa: F401 - Import to register
)

# Import all models to ensure SQLAlchemy metadata is properly registered
from workout_api.users.models import User  # noqa: F401
from workout_api.workouts.models import ExerciseExecution, Set, Workout  # noqa: F401


@dataclass
class SeederConfig:
    """Configuration for seeding operations."""

    dry_run: bool = False
    force: bool = False
    clean: bool = False
    csv_file: str | None = None


def setup_argument_parser() -> argparse.ArgumentParser:
    """Set up and configure the command line argument parser."""
    parser = argparse.ArgumentParser(
        description="Seed database with initial data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                                    # Seed all data to default database
  %(prog)s --seeders exercises                # Seed only exercises
  %(prog)s --database-url postgresql://...    # Seed to specific database
  %(prog)s --dry-run --verbose               # See what would be seeded
  %(prog)s --force                           # Force reseed (skip existing checks)
  %(prog)s --list                            # List available seeders
        """,
    )

    parser.add_argument(
        "--database-url",
        help="Database URL to seed (overrides settings)",
    )

    parser.add_argument(
        "--seeders",
        help="Comma-separated list of seeders to run (default: all)",
    )

    parser.add_argument(
        "--list",
        action="store_true",
        help="List available seeders and exit",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be seeded without making changes",
    )

    parser.add_argument(
        "--force",
        action="store_true",
        help="Force seeding (skip existing item checks)",
    )

    parser.add_argument(
        "--clean",
        action="store_true",
        help="Clean (truncate) relevant tables before seeding",
    )

    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging",
    )

    parser.add_argument(
        "--csv-file",
        help="Path to CSV file for exercise seeder (optional)",
    )

    return parser


def setup_logging(verbose: bool) -> logging.Logger:
    """Set up logging configuration and return logger."""
    log_level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    return logging.getLogger(__name__)


def list_available_seeders() -> None:
    """List all available seeders and exit."""
    print("Available seeders:")
    for name in SeederRegistry.list_seeder_names():
        print(f"  - {name}")


async def initialize_database(
    database_url_override: str | None,
) -> tuple[Settings, DatabaseManager]:
    """Initialize database connection and return settings and manager."""
    logger = logging.getLogger(__name__)

    # Override database URL if provided
    if database_url_override:
        os.environ["DATABASE_URL"] = database_url_override
        logger.info(f"Using database URL override: {database_url_override}")

    # Initialize settings and database
    try:
        settings = Settings()
        logger.info(f"Environment: {settings.environment}")

        # Special warning for production
        if settings.is_production:
            response = input(
                "⚠️  You are about to seed a PRODUCTION database. Are you sure? (type 'yes' to confirm): "
            )
            if response.lower() != "yes":
                print("Seeding cancelled.")
                sys.exit(0)

        db_manager = DatabaseManager()

        # Test database connection
        health = await db_manager.check_connection()
        if health["status"] != "healthy":
            logger.error(f"Database connection failed: {health}")
            sys.exit(1)

        logger.info("Database connection established")
        return settings, db_manager

    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        sys.exit(1)


def determine_and_validate_seeders(seeders_arg: str | None) -> list[str]:
    """Determine which seeders to run and validate they exist."""
    logger = logging.getLogger(__name__)

    # Determine which seeders to run
    if seeders_arg:
        seeder_names = [name.strip() for name in seeders_arg.split(",")]
    else:
        seeder_names = SeederRegistry.list_seeder_names()

    if not seeder_names:
        logger.error("No seeders available")
        sys.exit(1)

    # Validate seeder names
    invalid_seeders = [
        name for name in seeder_names if not SeederRegistry.is_registered(name)
    ]
    if invalid_seeders:
        logger.error(f"Unknown seeders: {invalid_seeders}")
        logger.error(f"Available seeders: {SeederRegistry.list_seeder_names()}")
        sys.exit(1)

    return seeder_names


async def run_seeders(
    db_manager: DatabaseManager,
    seeder_names: list[str],
    config: SeederConfig,
) -> list[SeedResult]:
    """Run the specified seeders and return results."""
    logger = logging.getLogger(__name__)

    logger.info(f"Running seeders: {seeder_names}")
    if config.dry_run:
        logger.info("🔍 DRY RUN MODE - No changes will be made")
    if config.force:
        logger.info("💪 FORCE MODE - Existing items will be overwritten")
    if config.clean:
        logger.info("🧹 CLEAN MODE - Tables will be truncated before seeding")

    all_results = []

    async with db_manager.get_session_context() as session:
        for seeder_name in seeder_names:
            logger.info(f"\n{'=' * 50}")
            logger.info(f"Running seeder: {seeder_name}")
            logger.info(f"{'=' * 50}")

            try:
                seeder_class = SeederRegistry.get_seeder(seeder_name)
                seeder = seeder_class(
                    session, dry_run=config.dry_run, force=config.force
                )

                # Clean tables if requested
                clean_result = None
                if config.clean:
                    logger.info(f"Cleaning tables for {seeder_name}...")
                    clean_result = await seeder.clean()
                    logger.info(f"Clean result: {clean_result}")

                # Pass additional arguments based on seeder type
                kwargs = {}
                if seeder_name == "exercises" and config.csv_file:
                    kwargs["csv_file_path"] = config.csv_file

                result = await seeder.seed(**kwargs)

                # Attach clean result to seed result
                if clean_result:
                    result.clean_result = clean_result

                all_results.append(result)
                logger.info(f"Seeder result: {result}")

            except Exception as e:
                logger.error(f"Seeder '{seeder_name}' failed: {e}")
                # Continue with other seeders rather than failing completely

    return all_results


def print_summary(results: list[SeedResult]) -> None:
    """Print the final seeding summary and exit with appropriate code."""
    print(f"\n{'=' * 60}")
    print("SEEDING SUMMARY")
    print(f"{'=' * 60}")

    total_created = sum(r.created_items for r in results)
    total_updated = sum(r.updated_items for r in results)
    total_skipped = sum(r.skipped_items for r in results)
    total_errors = sum(len(r.errors) for r in results)
    total_cleaned = sum(
        r.clean_result.rows_deleted if r.clean_result else 0 for r in results
    )

    for result in results:
        print(result)

    print(
        f"\nOverall: {total_cleaned} cleaned, {total_created} created, {total_updated} updated, {total_skipped} skipped, {total_errors} errors"
    )

    if total_errors > 0:
        print("\n❌ Seeding completed with errors")
        sys.exit(1)
    else:
        print("\n✅ Seeding completed successfully")


async def main() -> None:
    """Main CLI function."""
    # Parse arguments
    parser = setup_argument_parser()
    args = parser.parse_args()

    # Set up logging
    setup_logging(args.verbose)

    # List seeders if requested
    if args.list:
        list_available_seeders()
        return

    # Initialize database
    settings, db_manager = await initialize_database(args.database_url)

    # Determine and validate seeders
    seeder_names = determine_and_validate_seeders(args.seeders)

    # Run seeders
    config = SeederConfig(
        dry_run=args.dry_run,
        force=args.force,
        clean=args.clean,
        csv_file=args.csv_file,
    )
    results = await run_seeders(
        db_manager=db_manager,
        seeder_names=seeder_names,
        config=config,
    )

    # Print summary and exit
    print_summary(results)


if __name__ == "__main__":
    asyncio.run(main())
