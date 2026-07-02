"""Stub microphone provider for tests."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator

from app.voice.utils.audio import generate_silence_pcm


class StubMicrophone:
    """In-memory microphone that yields configurable PCM chunks."""

    def __init__(
        self,
        *,
        sample_rate: int = 16000,
        chunk_ms: int = 100,
        chunks: list[bytes] | None = None,
    ) -> None:
        """Initialize stub microphone."""
        self._sample_rate = sample_rate
        self._chunk_ms = chunk_ms
        self._chunks = chunks or [
            generate_silence_pcm(chunk_ms, sample_rate=sample_rate) for _ in range(5)
        ]
        self._running = False
        self._queue: asyncio.Queue[bytes] = asyncio.Queue()

    @property
    def provider_name(self) -> str:
        """Return provider identifier."""
        return "stub"

    @property
    def sample_rate(self) -> int:
        """Return capture sample rate."""
        return self._sample_rate

    async def health_check(self) -> bool:
        """Stub microphone is always healthy."""
        return True

    async def list_devices(self) -> list[dict[str, str | int]]:
        """Return a single virtual device."""
        return [{"index": 0, "name": "stub-microphone"}]

    async def start(self) -> None:
        """Begin virtual capture."""
        self._running = True
        for chunk in self._chunks:
            await self._queue.put(chunk)

    async def stop(self) -> None:
        """Stop virtual capture."""
        self._running = False

    async def push_chunk(self, chunk: bytes) -> None:
        """Push an audio chunk into the stub stream."""
        await self._queue.put(chunk)

    def stream(self) -> AsyncIterator[bytes]:
        """Yield queued PCM chunks."""
        return self._stream_impl()

    async def _stream_impl(self) -> AsyncIterator[bytes]:
        """Internal async generator for PCM chunks."""
        while self._running:
            try:
                chunk = await asyncio.wait_for(self._queue.get(), timeout=0.2)
            except TimeoutError:
                continue
            yield chunk
