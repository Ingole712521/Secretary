"""Health and status reporting service."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.models.health import (
    HealthResponse,
    RootResponse,
    VersionResponse,
)
from app.services.base import BaseService
from app.utils.date import utc_timestamp_iso

if TYPE_CHECKING:
    from app.config.settings import Settings


class HealthService(BaseService):
    """Provides health, version, and root status information."""

    def __init__(self, settings: Settings) -> None:
        """Initialize the health service.

        Args:
            settings: Application configuration.
        """
        super().__init__(settings)

    def get_root(self) -> RootResponse:
        """Return root API welcome payload.

        Returns:
            Root response with application metadata.
        """
        return RootResponse(
            name=self._settings.app_name,
            version=self._settings.app_version,
            environment=self._settings.app_env.value,
            docs="/docs",
        )

    def get_health(self) -> HealthResponse:
        """Return application health status.

        Returns:
            Health response indicating service is operational.
        """
        return HealthResponse(
            status="ok",
            environment=self._settings.app_env.value,
            timestamp=utc_timestamp_iso(),
        )

    def get_version(self) -> VersionResponse:
        """Return application version information.

        Returns:
            Version response with name and version.
        """
        return VersionResponse(
            name=self._settings.app_name,
            version=self._settings.app_version,
            environment=self._settings.app_env.value,
        )
