"""Middleware registration for the FastAPI application."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.middleware.cors import configure_cors
from app.middleware.logging import RequestLoggingMiddleware
from app.middleware.request_id import RequestIdMiddleware

if TYPE_CHECKING:
    from fastapi import FastAPI

    from app.config.settings import Settings


def configure_middleware(app: FastAPI, settings: Settings) -> None:
    """Register all HTTP middleware in correct execution order.

    Starlette executes the last-registered middleware first on incoming
    requests. Order here (first to last registered):

    1. Request logging (innermost)
    2. Request ID
    3. CORS (outermost)

    Args:
        app: FastAPI application.
        settings: Application settings.
    """
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(RequestIdMiddleware, settings=settings)
    configure_cors(app, settings)
