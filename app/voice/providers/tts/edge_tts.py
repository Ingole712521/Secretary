"""Microsoft Edge text-to-speech provider."""

from __future__ import annotations

import asyncio
import io
import logging
from collections.abc import AsyncIterator

from app.config.settings import Settings
from app.constants import LOGGER_ROOT
from app.voice.exceptions import TextToSpeechError
from app.voice.schemas.models import SynthesisOptions, SynthesisResult

logger = logging.getLogger(f"{LOGGER_ROOT}.voice.tts.edge")


class EdgeTextToSpeech:
    """Free TTS using the edge-tts library."""

    def __init__(self, settings: Settings) -> None:
        """Initialize Edge TTS provider."""
        self._settings = settings

    @property
    def provider_name(self) -> str:
        """Return provider identifier."""
        return "edge_tts"

    async def health_check(self) -> bool:
        """Return True when edge-tts is importable."""
        try:
            import edge_tts  # noqa: F401
        except ImportError:
            return False
        return True

    async def synthesize(
        self,
        text: str,
        *,
        options: SynthesisOptions | None = None,
    ) -> SynthesisResult:
        """Synthesize speech using edge-tts."""
        if not text.strip():
            raise TextToSpeechError("Cannot synthesize empty text")
        try:
            audio = await asyncio.to_thread(self._synthesize_sync, text, options)
        except ImportError as exc:
            raise TextToSpeechError("edge-tts is not installed") from exc
        except Exception as exc:  # noqa: BLE001
            raise TextToSpeechError(f"Edge TTS failed: {exc}") from exc

        return SynthesisResult(audio=audio, format="mp3", provider=self.provider_name)

    async def synthesize_stream(
        self,
        text: str,
        *,
        options: SynthesisOptions | None = None,
    ) -> AsyncIterator[bytes]:
        """Yield MP3 chunks from edge-tts."""
        if not text.strip():
            raise TextToSpeechError("Cannot synthesize empty text")
        try:
            import edge_tts
        except ImportError as exc:
            raise TextToSpeechError("edge-tts is not installed") from exc

        voice = (
            options.voice
            if options and options.voice
            else self._settings.edge_tts_voice
        )
        communicate = edge_tts.Communicate(text, voice)
        for chunk in communicate.stream_sync():
            if chunk["type"] == "audio":
                yield chunk["data"]

    def _synthesize_sync(self, text: str, options: SynthesisOptions | None) -> bytes:
        """Synchronously generate MP3 audio with edge-tts."""
        import edge_tts

        voice = (
            options.voice
            if options and options.voice
            else self._settings.edge_tts_voice
        )
        communicate = edge_tts.Communicate(text, voice)
        buffer = io.BytesIO()
        for chunk in communicate.stream_sync():
            if chunk["type"] == "audio":
                buffer.write(chunk["data"])
        audio = buffer.getvalue()
        if not audio:
            raise TextToSpeechError("Edge TTS produced no audio")
        return audio
