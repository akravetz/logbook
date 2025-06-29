"""Logging configuration for the application."""

import logging
import logging.config
import sys
from pathlib import Path
from typing import Any

from .config import get_settings


def setup_logging() -> None:
    """Configure logging for the application."""
    settings = get_settings()

    # Create logs directory if it doesn't exist
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)

    # Configure logging
    logging_config = get_logging_config(settings)
    logging.config.dictConfig(logging_config)

    # Log startup information
    logger = logging.getLogger(__name__)
    logger.info(
        f"Logging initialized - Level: {settings.log_level}, Environment: {settings.environment}"
    )


def get_logging_config(settings) -> dict[str, Any]:
    """Get logging configuration dictionary."""

    # Base formatter
    base_formatter = {
        "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        "datefmt": "%Y-%m-%d %H:%M:%S",
    }

    # JSON formatter for production
    json_formatter = {
        "format": '{"timestamp": "%(asctime)s", "logger": "%(name)s", "level": "%(levelname)s", "message": "%(message)s", "module": "%(module)s", "function": "%(funcName)s", "line": %(lineno)d}',
        "datefmt": "%Y-%m-%dT%H:%M:%S",
    }

    config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": base_formatter,
            "json": json_formatter,
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": settings.log_level,
                "formatter": "json" if settings.is_production else "standard",
                "stream": sys.stdout,
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": settings.log_level,
                "formatter": "json" if settings.is_production else "standard",
                "filename": "logs/app.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
                "encoding": "utf8",
            },
            "error_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "ERROR",
                "formatter": "json" if settings.is_production else "standard",
                "filename": "logs/error.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
                "encoding": "utf8",
            },
        },
        "loggers": {
            "workout_api": {
                "level": settings.log_level,
                "handlers": ["console", "file", "error_file"],
                "propagate": False,
            },
            "sqlalchemy.engine": {
                "level": "INFO" if settings.debug else "WARNING",
                "handlers": ["console", "file"],
                "propagate": False,
            },
            "sqlalchemy.pool": {
                "level": "INFO" if settings.debug else "WARNING",
                "handlers": ["console", "file"],
                "propagate": False,
            },
            "uvicorn": {
                "level": "INFO",
                "handlers": ["console", "file"],
                "propagate": False,
            },
            "uvicorn.access": {
                "level": "INFO",
                "handlers": ["console", "file"],
                "propagate": False,
            },
        },
        "root": {
            "level": "INFO",
            "handlers": ["console", "file"],
        },
    }

    # In development, also log to console with more detail
    if settings.is_development:
        config["handlers"]["console"]["formatter"] = "standard"
        config["loggers"]["workout_api"]["level"] = "DEBUG"

    return config


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance for the given name."""
    return logging.getLogger(f"workout_api.{name}")


# Convenience loggers
app_logger = get_logger("app")
db_logger = get_logger("database")
auth_logger = get_logger("auth")
api_logger = get_logger("api")
