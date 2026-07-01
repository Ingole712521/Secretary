"""FastAPI application factory and lifecycle management."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.router import api_router
from app.config.settings import Settings, get_settings
from app.core.logging import setup_logging
from app.dependencies.container import build_container
from app.middleware.cors import configure_cors
from app.middleware.error_handling import register_exception_handlers
from app.middleware.logging import RequestLoggingMiddleware
from app.middleware.request_id import RequestIdMiddleware
from app.utils.file import ensure_directory


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Manage application startup and shutdown events.

    Args:
        app: FastAPI application instance.

    Yields:
        Control to the running application.
    """
    settings: Settings = app.state.settings
    logger_name = "jarvis.startup"

    import logging

    logger = logging.getLogger(logger_name)
    ensure_directory(settings.log_dir)
    ensure_directory(settings.data_dir)
    app.state.container = build_container(settings)

    logger.info(
        "Jarvis OS starting | env=%s version=%s",
        settings.app_env.value,
        settings.app_version,
    )

    yield

    logger.info("Jarvis OS shutting down")


def create_app(settings: Settings | None = None) -> FastAPI:
    """Create and configure the FastAPI application.

    Args:
        settings: Optional settings override (used in tests).

    Returns:
        Configured FastAPI application.
    """
    resolved_settings = settings or get_settings()
    setup_logging(resolved_settings)

    app = FastAPI(
        title=resolved_settings.app_name,
        version=resolved_settings.app_version,
        debug=resolved_settings.debug,
        lifespan=lifespan,
        docs_url="/docs" if not resolved_settings.is_production else None,
        redoc_url="/redoc" if not resolved_settings.is_production else None,
    )

    app.state.settings = resolved_settings
    app.state.container = build_container(resolved_settings)

    register_exception_handlers(app, resolved_settings)
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(RequestIdMiddleware, settings=resolved_settings)
    configure_cors(app, resolved_settings)
    app.include_router(api_router)

    return app
