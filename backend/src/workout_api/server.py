"""Server script that uses settings for configuration."""

import asyncio

import hypercorn.asyncio

from .core.main import app, get_hypercorn_config


def main() -> None:
    """Run the server with hypercorn configuration."""
    config = get_hypercorn_config()
    asyncio.run(hypercorn.asyncio.serve(app, config))


if __name__ == "__main__":
    main()
