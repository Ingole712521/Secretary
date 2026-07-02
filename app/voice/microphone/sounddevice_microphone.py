"""Sounddevice microphone provider."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncIterator
from typing import TYPE_CHECKING, Any, cast

from app.constants import LOGGER_ROOT
from app.voice.exceptions import MicrophoneError

if TYPE_CHECKING:
    from app.config.settings import Settings

logger = logging.getLogger(f"{LOGGER_ROOT}.voice.microphone")


class SounddeviceMicrophone:
    """Microphone capture using the sounddevice library."""

    def __init__(self, settings: Settings) -> None:
        """Initialize sounddevice microphone."""
        self._settings = settings
        self._running = False
        self._queue: asyncio.Queue[bytes] = asyncio.Queue()
        self._stream: object | None = None

    @property
    def provider_name(self) -> str:
        """Return provider identifier."""
        return "sounddevice"

    @property
    def sample_rate(self) -> int:
        """Return capture sample rate."""
        return self._settings.voice_sample_rate

    async def health_check(self) -> bool:
        """Return True when sounddevice is importable."""
        try:
            import sounddevice  # noqa: F401
        except ImportError:
            return False
        return True

    async def list_devices(self) -> list[dict[str, str | int]]:
        """Return available input devices."""
        try:
            import sounddevice as sd
        except ImportError as exc:
            raise MicrophoneError("sounddevice is not installed") from exc

        devices: list[dict[str, str | int]] = []
        for index, device in enumerate(sd.query_devices()):
            if device["max_input_channels"] > 0:
                devices.append({"index": index, "name": device["name"]})
        return devices

    async def start(self) -> None:
        """Start microphone capture."""
        try:
            import sounddevice as sd
        except ImportError as exc:
            raise MicrophoneError("sounddevice is not installed") from exc

        device = self._resolve_device()
        self._running = True

        def callback(
            indata: Any,
            _frames: int,
            _time: Any,
            _status: Any,
        ) -> None:
            if self._running:
                self._queue.put_nowait(bytes(indata))

        stream = sd.RawInputStream(
            samplerate=self.sample_rate,
            channels=1,
            dtype="int16",
            device=device,
            callback=callback,
            blocksize=int(self.sample_rate * 0.1),
        )
        self._stream = stream
        cast(Any, stream).start()
        logger.info("Microphone started | device=%s", device)

    async def stop(self) -> None:
        """Stop microphone capture."""
        self._running = False
        if self._stream is not None:
            self._stream.stop()  # type: ignore[attr-defined]
            self._stream.close()  # type: ignore[attr-defined]
            self._stream = None

    def stream(self) -> AsyncIterator[bytes]:
        """Yield PCM chunks from the capture queue."""
        return self._stream_impl()

    async def _stream_impl(self) -> AsyncIterator[bytes]:
        """Internal async generator for microphone chunks."""
        while self._running:
            try:
                chunk = await asyncio.wait_for(self._queue.get(), timeout=0.2)
            except TimeoutError:
                continue
            yield chunk

    def _resolve_device(self) -> int | str | None:
        """Resolve configured microphone device."""
        device = self._settings.voice_microphone_device
        if device is None:
            return None
        if device.isdigit():
            return int(device)
        return device
