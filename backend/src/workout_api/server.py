"""Server script that uses settings for configuration."""

import uvicorn

from .core.main import get_server_config


def main() -> None:
    """Run the server with configuration from settings."""
    config = get_server_config()
    uvicorn.run("workout_api.core.main:app", **config)


if __name__ == "__main__":
    main()
