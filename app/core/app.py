"""FastAPI application factory and lifecycle management."""

from __future__ import annotations

from fastapi import FastAPI

from app.api.router import api_router
from app.config.settings import Settings, get_settings
from app.core.lifespan import lifespan
from app.core.logging import setup_logging
from app.core.middleware_setup import configure_middleware
from app.dependencies.container import build_container
from app.middleware.error_handling import register_exception_handlers


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
    configure_middleware(app, resolved_settings)
    app.include_router(api_router)

    return app
