"""CORS configuration."""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

if TYPE_CHECKING:
    from app.config.settings import Settings

_PRODUCTION_METHODS = ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]
_PRODUCTION_HEADERS = [
    "Authorization",
    "Content-Type",
    "Accept",
    "X-Correlation-ID",
]


def configure_cors(app: FastAPI, settings: Settings) -> None:
    """Register CORS middleware with environment-appropriate restrictions.

    Production uses explicit methods and headers. Non-production allows
    broader access to simplify local development.

    Args:
        app: FastAPI application.
        settings: Application settings.
    """
    if settings.is_production:
        allow_methods: list[str] = _PRODUCTION_METHODS
        allow_headers: list[str] = [
            *{settings.correlation_id_header, *_PRODUCTION_HEADERS},
        ]
    else:
        allow_methods = ["*"]
        allow_headers = ["*"]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=allow_methods,
        allow_headers=allow_headers,
        expose_headers=[settings.correlation_id_header],
    )
