"""Queued audio output player."""

from __future__ import annotations

import asyncio
import contextlib
import logging
from typing import TYPE_CHECKING

from app.constants import LOGGER_ROOT
from app.voice.exceptions import AudioOutputError

if TYPE_CHECKING:
    from app.config.settings import Settings

logger = logging.getLogger(f"{LOGGER_ROOT}.voice.audio")


class QueueAudioPlayer:
    """Audio output with queueing, interruption, and volume control."""

    def __init__(self, settings: Settings) -> None:
        """Initialize queue audio player."""
        self._settings = settings
        self._volume = 1.0
        self._queue: asyncio.Queue[tuple[bytes, str, int | None]] = asyncio.Queue()
        self._worker: asyncio.Task[None] | None = None
        self._current_task: asyncio.Task[None] | None = None
        self._running = False

    @property
    def provider_name(self) -> str:
        """Return provider identifier."""
        return "queue_player"

    async def health_check(self) -> bool:
        """Return True when sounddevice is available for playback."""
        try:
            import sounddevice  # noqa: F401
        except ImportError:
            return False
        return True

    async def play(
        self,
        audio: bytes,
        *,
        audio_format: str = "wav",
        sample_rate: int | None = None,
        volume: float = 1.0,
    ) -> None:
        """Interrupt current playback and play immediately."""
        await self.interrupt()
        await self._play_audio(
            audio,
            audio_format=audio_format,
            sample_rate=sample_rate,
            volume=volume,
        )

    async def enqueue(
        self,
        audio: bytes,
        *,
        audio_format: str = "wav",
        sample_rate: int | None = None,
        volume: float = 1.0,
    ) -> None:
        """Queue audio for sequential playback."""
        if not self._running:
            self._running = True
            self._worker = asyncio.create_task(self._worker_loop())
        await self._queue.put((audio, audio_format, sample_rate))

    async def interrupt(self) -> None:
        """Stop current playback and clear queue."""
        while not self._queue.empty():
            self._queue.get_nowait()
        if self._current_task is not None:
            self._current_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._current_task
            self._current_task = None

    async def set_volume(self, volume: float) -> None:
        """Set global playback volume."""
        if volume < 0:
            raise AudioOutputError("Volume must be non-negative")
        self._volume = volume

    async def shutdown(self) -> None:
        """Stop worker and release resources."""
        self._running = False
        await self.interrupt()
        if self._worker is not None:
            self._worker.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._worker
            self._worker = None

    async def _worker_loop(self) -> None:
        """Process queued playback requests."""
        while self._running:
            audio, audio_format, sample_rate = await self._queue.get()
            self._current_task = asyncio.create_task(
                self._play_audio(
                    audio,
                    audio_format=audio_format,
                    sample_rate=sample_rate,
                    volume=self._volume,
                ),
            )
            try:
                await self._current_task
            finally:
                self._current_task = None

    async def _play_audio(
        self,
        audio: bytes,
        *,
        audio_format: str,
        sample_rate: int | None,
        volume: float,
    ) -> None:
        """Play audio using sounddevice when available."""
        _ = audio_format
        try:
            import numpy as np
            import sounddevice as sd
        except ImportError as exc:
            raise AudioOutputError(
                "sounddevice is required for audio playback",
            ) from exc

        pcm, rate = self._extract_pcm(audio, sample_rate=sample_rate)
        samples = np.frombuffer(pcm, dtype=np.int16).astype(np.float32) / 32768.0
        samples *= min(max(volume, 0.0), 2.0)
        device = self._resolve_device()
        await asyncio.to_thread(sd.play, samples, rate, device=device)
        await asyncio.to_thread(sd.wait)

    def _extract_pcm(
        self,
        audio: bytes,
        *,
        sample_rate: int | None,
    ) -> tuple[bytes, int]:
        """Extract PCM bytes and sample rate from audio payload."""
        if audio[:4] == b"RIFF":
            rate = sample_rate or self._settings.voice_sample_rate
            return audio[44:], rate
        return audio, sample_rate or self._settings.voice_sample_rate

    def _resolve_device(self) -> int | str | None:
        """Resolve configured speaker device."""
        device = self._settings.voice_speaker_device
        if device is None:
            return None
        if device.isdigit():
            return int(device)
        return device
