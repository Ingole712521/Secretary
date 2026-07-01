"""Base class for application services."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.config.settings import Settings


class BaseService:
    """Base class providing shared access to application settings."""

    def __init__(self, settings: Settings) -> None:
        """Initialize the service with settings.

        Args:
            settings: Application configuration.
        """
        self._settings = settings

    @property
    def settings(self) -> Settings:
        """Return application settings."""
        return self._settings
