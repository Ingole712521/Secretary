"""Stub audio output provider for tests."""

from __future__ import annotations

from app.voice.exceptions import AudioOutputError


class StubAudioOutput:
    """Records playback requests without emitting sound."""

    def __init__(self) -> None:
        """Initialize stub audio output."""
        self.played: list[bytes] = []
        self.queued: list[bytes] = []
        self.volume = 1.0
        self.interrupted = False

    @property
    def provider_name(self) -> str:
        """Return provider identifier."""
        return "stub"

    async def health_check(self) -> bool:
        """Stub audio output is always healthy."""
        return True

    async def play(
        self,
        audio: bytes,
        *,
        audio_format: str = "wav",
        sample_rate: int | None = None,
        volume: float = 1.0,
    ) -> None:
        """Record immediate playback."""
        _ = audio_format, sample_rate, volume
        self.interrupted = False
        self.played.append(audio)

    async def enqueue(
        self,
        audio: bytes,
        *,
        audio_format: str = "wav",
        sample_rate: int | None = None,
        volume: float = 1.0,
    ) -> None:
        """Record queued playback."""
        _ = audio_format, sample_rate, volume
        self.queued.append(audio)

    async def interrupt(self) -> None:
        """Mark playback as interrupted."""
        self.interrupted = True
        self.queued.clear()

    async def set_volume(self, volume: float) -> None:
        """Set playback volume."""
        if volume < 0:
            raise AudioOutputError("Volume must be non-negative")
        self.volume = volume
