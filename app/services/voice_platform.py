"""Voice platform application service."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.services.base import BaseService
from app.voice.exceptions import VoiceLifecycleError, VoiceNotAvailableError
from app.voice.schemas.status import VoicePlatformStatus

if TYPE_CHECKING:
    from app.voice.factory import VoicePlatformContainer


class VoicePlatformService(BaseService):
    """Application service for voice platform lifecycle control."""

    def __init__(
        self,
        settings: object,
        platform: VoicePlatformContainer,
    ) -> None:
        """Initialize voice platform service."""
        super().__init__(settings)  # type: ignore[arg-type]
        self._platform = platform

    @property
    def manager(self) -> object:
        """Return the underlying voice manager."""
        return self._platform.manager

    async def start(self) -> VoicePlatformStatus:
        """Start the voice platform."""
        if not self._settings.voice_enabled:
            raise VoiceNotAvailableError("Voice interaction is disabled")
        try:
            await self._platform.manager.start()
        except VoiceLifecycleError as exc:
            raise VoiceNotAvailableError(exc.message) from exc
        return await self._platform.manager.get_status()

    async def stop(self) -> VoicePlatformStatus:
        """Stop the voice platform."""
        await self._platform.manager.stop()
        return await self._platform.manager.get_status()

    async def pause(self) -> VoicePlatformStatus:
        """Pause wake word listening."""
        await self._platform.manager.pause()
        return await self._platform.manager.get_status()

    async def resume(self) -> VoicePlatformStatus:
        """Resume wake word listening."""
        await self._platform.manager.resume()
        return await self._platform.manager.get_status()

    async def status(self) -> VoicePlatformStatus:
        """Return current voice platform status."""
        return await self._platform.manager.get_status()

    async def shutdown(self) -> None:
        """Shutdown the voice platform."""
        await self._platform.manager.shutdown()
