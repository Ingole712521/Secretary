"""Audio output port."""

from __future__ import annotations

from typing import Protocol


class AudioOutput(Protocol):
    """Port for playing synthesized speech."""

    @property
    def provider_name(self) -> str:
        """Return the audio output provider identifier."""
        ...

    async def health_check(self) -> bool:
        """Return True when audio output is available."""
        ...

    async def play(
        self,
        audio: bytes,
        *,
        audio_format: str = "wav",
        sample_rate: int | None = None,
        volume: float = 1.0,
    ) -> None:
        """Play audio immediately, interrupting current playback.

        Args:
            audio: Raw audio bytes.
            audio_format: Container/codec hint.
            sample_rate: Optional PCM sample rate.
            volume: Playback volume multiplier.
        """
        ...

    async def enqueue(
        self,
        audio: bytes,
        *,
        audio_format: str = "wav",
        sample_rate: int | None = None,
        volume: float = 1.0,
    ) -> None:
        """Queue audio for sequential playback."""
        ...

    async def interrupt(self) -> None:
        """Stop current playback and clear the queue."""
        ...

    async def set_volume(self, volume: float) -> None:
        """Set the global playback volume."""
        ...
