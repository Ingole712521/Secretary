"""Jarvis OS application entry point.

Starts the FastAPI application with logging, middleware, routes,
configuration loading, and lifecycle event handling.
"""

from __future__ import annotations

import logging

import uvicorn

from app.config.settings import get_settings
from app.constants import LOGGER_MAIN
from app.core.app import create_app

settings = get_settings()
app = create_app(settings)

logger = logging.getLogger(LOGGER_MAIN)


def main() -> None:
    """Run the application with Uvicorn."""
    logger.info(
        "Starting Uvicorn | host=%s port=%s env=%s",
        settings.api_host,
        settings.api_port,
        settings.app_env.value,
    )
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.is_development,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    main()
