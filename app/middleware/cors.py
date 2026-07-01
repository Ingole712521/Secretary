"""CORS configuration."""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

if TYPE_CHECKING:
    from app.config.settings import Settings


def configure_cors(app: FastAPI, settings: Settings) -> None:
    """Register CORS middleware with configured origins.

    Args:
        app: FastAPI application.
        settings: Application settings.
    """
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=[settings.correlation_id_header],
    )
