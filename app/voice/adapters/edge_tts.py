"""Microsoft Edge text-to-speech adapter."""

from __future__ import annotations

import asyncio
import io
import logging

from app.config.settings import Settings
from app.constants import LOGGER_ROOT
from app.voice.exceptions import TextToSpeechError
from app.voice.schemas.models import SynthesisResult

logger = logging.getLogger(f"{LOGGER_ROOT}.voice.tts")


class EdgeTextToSpeech:
    """Free TTS using the ``edge-tts`` library (Microsoft Edge voices).

    Attributes:
        _settings: Application settings.
    """

    def __init__(self, settings: Settings) -> None:
        """Initialize Edge TTS adapter.

        Args:
            settings: Application settings with voice name.
        """
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

    async def synthesize(self, text: str) -> SynthesisResult:
        """Synthesize speech using edge-tts."""
        if not text.strip():
            raise TextToSpeechError("Cannot synthesize empty text")

        try:
            audio = await asyncio.to_thread(self._synthesize_sync, text)
        except ImportError as exc:
            raise TextToSpeechError("edge-tts is not installed") from exc
        except Exception as exc:  # noqa: BLE001
            raise TextToSpeechError(f"Edge TTS failed: {exc}") from exc

        logger.info("Edge TTS success | chars=%d bytes=%d", len(text), len(audio))
        return SynthesisResult(
            audio=audio,
            format="mp3",
            provider=self.provider_name,
        )

    def _synthesize_sync(self, text: str) -> bytes:
        """Synchronously generate MP3 audio with edge-tts."""
        import edge_tts

        communicate = edge_tts.Communicate(text, self._settings.edge_tts_voice)
        buffer = io.BytesIO()
        for chunk in communicate.stream_sync():
            if chunk["type"] == "audio":
                buffer.write(chunk["data"])
        audio = buffer.getvalue()
        if not audio:
            raise TextToSpeechError("Edge TTS produced no audio")
        return audio
