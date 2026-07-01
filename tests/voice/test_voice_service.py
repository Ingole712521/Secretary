"""VoiceService unit tests."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from app.config.settings import Environment, Settings
from app.exceptions import ConfigurationException
from app.models.chat import ChatResponse
from app.services.voice import VoiceService
from app.voice.adapters.stub_stt import StubSpeechToText
from app.voice.adapters.stub_tts import StubTextToSpeech
from app.voice.exceptions import VoiceNotAvailableError


def _voice_settings(tmp_path: object, **overrides: object) -> Settings:
    """Build testing settings with stub voice providers."""
    defaults: dict[str, object] = {
        "_env_file": None,
        "app_env": Environment.TESTING,
        "debug": True,
        "log_dir": tmp_path / "logs",  # type: ignore[operator]
        "data_dir": tmp_path / "data",  # type: ignore[operator]
        "api_secret_key": "test-secret-key",
        "voice_enabled": True,
        "voice_stt_provider": "stub",
        "voice_tts_provider": "stub",
    }
    defaults.update(overrides)
    return Settings(**defaults)  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_process_turn_returns_transcript_and_audio(tmp_path: object) -> None:
    """VoiceService orchestrates STT → chat → TTS."""
    settings = _voice_settings(tmp_path)
    chat_service = AsyncMock()
    chat_service.chat = AsyncMock(
        return_value=ChatResponse(
            message="Hello Nehal.",
            conversation_id="conv-abc",
            model="anthropic/claude-3.5-sonnet",
            provider="openrouter",
        ),
    )
    service = VoiceService(
        settings,
        chat_service,
        StubSpeechToText(transcript="hello jarvis"),
        StubTextToSpeech(audio=b"reply-audio", audio_format="mp3"),
    )

    result = await service.process_turn(b"fake-audio", audio_format="wav")

    assert result.transcript == "hello jarvis"
    assert result.response_text == "Hello Nehal."
    assert result.conversation_id == "conv-abc"
    assert result.audio_format == "mp3"
    assert result.response_audio_base64


@pytest.mark.asyncio
async def test_process_turn_raises_when_voice_disabled(tmp_path: object) -> None:
    """VoiceService rejects turns when voice is disabled."""
    settings = _voice_settings(tmp_path, voice_enabled=False)
    chat_service = AsyncMock()
    service = VoiceService(
        settings,
        chat_service,
        StubSpeechToText(),
        StubTextToSpeech(),
    )

    with pytest.raises(VoiceNotAvailableError, match="disabled"):
        await service.process_turn(b"audio")


@pytest.mark.asyncio
async def test_process_turn_maps_configuration_error(tmp_path: object) -> None:
    """Chat configuration errors surface as voice unavailable."""
    settings = _voice_settings(tmp_path)
    chat_service = AsyncMock()
    chat_service.chat = AsyncMock(
        side_effect=ConfigurationException("LLM not configured"),
    )
    service = VoiceService(
        settings,
        chat_service,
        StubSpeechToText(),
        StubTextToSpeech(),
    )

    with pytest.raises(VoiceNotAvailableError, match="LLM not configured"):
        await service.process_turn(b"audio")


@pytest.mark.asyncio
async def test_is_available_with_stub_providers(tmp_path: object) -> None:
    """Stub STT/TTS adapters report voice as available."""
    settings = _voice_settings(tmp_path)
    service = VoiceService(
        settings,
        AsyncMock(),
        StubSpeechToText(),
        StubTextToSpeech(),
    )

    assert await service.is_available() is True
