"""Microphone capture port."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Protocol


class Microphone(Protocol):
    """Port for capturing audio from an input device."""

    @property
    def provider_name(self) -> str:
        """Return the microphone provider identifier."""
        ...

    @property
    def sample_rate(self) -> int:
        """Return the capture sample rate in Hz."""
        ...

    async def health_check(self) -> bool:
        """Return True when the microphone is available."""
        ...

    async def list_devices(self) -> list[dict[str, str | int]]:
        """Return available input devices."""
        ...

    async def start(self) -> None:
        """Begin capturing audio."""
        ...

    async def stop(self) -> None:
        """Stop capturing audio."""
        ...

    def stream(self) -> AsyncIterator[bytes]:
        """Yield PCM audio chunks while capturing."""
        ...
