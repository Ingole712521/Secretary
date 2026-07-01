"""Application startup and shutdown lifecycle."""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config.settings import Settings
from app.constants import LOGGER_STARTUP
from app.utils.file import ensure_directory

logger = logging.getLogger(LOGGER_STARTUP)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Manage application startup and shutdown events.

    Args:
        app: FastAPI application instance.

    Yields:
        Control to the running application.
    """
    settings: Settings = app.state.settings
    ensure_directory(settings.log_dir)
    ensure_directory(settings.data_dir)

    logger.info(
        "Jarvis OS starting | env=%s version=%s",
        settings.app_env.value,
        settings.app_version,
    )

    yield

    container = app.state.container
    if container.brain.openrouter_provider is not None:
        await container.brain.openrouter_provider.close()

    logger.info("Jarvis OS shutting down")
