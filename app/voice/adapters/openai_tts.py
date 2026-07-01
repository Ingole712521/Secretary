"""OpenAI text-to-speech adapter."""

from __future__ import annotations

import logging

import httpx

from app.config.settings import Settings
from app.constants import LOGGER_ROOT
from app.voice.exceptions import TextToSpeechError, VoiceNotAvailableError
from app.voice.schemas.models import SynthesisResult

logger = logging.getLogger(f"{LOGGER_ROOT}.voice.tts")

_DEFAULT_TIMEOUT = httpx.Timeout(60.0, connect=10.0)


class OpenAiTts:
    """OpenAI TTS API adapter.

    Attributes:
        _settings: Application settings.
        _http_client: Optional injected HTTP client.
    """

    def __init__(
        self,
        settings: Settings,
        *,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        """Initialize OpenAI TTS adapter."""
        self._settings = settings
        self._http_client = http_client

    @property
    def provider_name(self) -> str:
        """Return provider identifier."""
        return "openai_tts"

    async def health_check(self) -> bool:
        """Return True when an OpenAI API key is configured."""
        return self._settings.get_voice_stt_api_key() is not None

    async def synthesize(self, text: str) -> SynthesisResult:
        """Synthesize speech via OpenAI TTS API."""
        if not text.strip():
            raise TextToSpeechError("Cannot synthesize empty text")

        api_key = self._require_api_key()
        url = f"{self._api_base()}/audio/speech"
        body = {
            "model": self._settings.openai_tts_model,
            "voice": self._settings.openai_tts_voice,
            "input": text,
            "response_format": "mp3",
        }

        try:
            client = await self._get_client()
            response = await client.post(
                url,
                headers={"Authorization": f"Bearer {api_key}"},
                json=body,
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            detail = exc.response.text or str(exc.response.status_code)
            raise TextToSpeechError(f"OpenAI TTS failed: {detail}") from exc
        except httpx.HTTPError as exc:
            raise TextToSpeechError(f"OpenAI TTS request failed: {exc}") from exc

        audio = response.content
        if not audio:
            raise TextToSpeechError("OpenAI TTS returned empty audio")

        logger.info("OpenAI TTS success | chars=%d bytes=%d", len(text), len(audio))
        return SynthesisResult(
            audio=audio,
            format="mp3",
            provider=self.provider_name,
        )

    def _require_api_key(self) -> str:
        """Return OpenAI API key or raise."""
        api_key = self._settings.get_voice_stt_api_key()
        if api_key is None:
            raise VoiceNotAvailableError(
                "OpenAI API key required for OpenAI TTS",
            )
        return api_key.get_secret_value()

    def _api_base(self) -> str:
        """Return OpenAI API base URL."""
        base = self._settings.openai_api_base or "https://api.openai.com/v1"
        return base.rstrip("/")

    async def _get_client(self) -> httpx.AsyncClient:
        """Return HTTP client."""
        if self._http_client is not None:
            return self._http_client
        return httpx.AsyncClient(timeout=_DEFAULT_TIMEOUT)
