"""Voice manager tests."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from app.config.settings import Environment, Settings
from app.models.chat import ChatResponse
from app.voice.audio.stub_audio_output import StubAudioOutput
from app.voice.conversation.controller import ConversationController
from app.voice.events import VoiceEventBus
from app.voice.factory import build_voice_platform
from app.voice.manager.voice_manager import VoiceManager
from app.voice.providers.stt.stub_stt import StubSpeechToText
from app.voice.providers.tts.stub_tts import StubTextToSpeech
from app.voice.schemas.models import VoiceLifecycleState


def _settings(tmp_path: object) -> Settings:
    return Settings(
        _env_file=None,
        app_env=Environment.TESTING,
        debug=True,
        log_dir=tmp_path / "logs",  # type: ignore[operator]
        data_dir=tmp_path / "data",  # type: ignore[operator]
        api_secret_key="test-secret-key",
        voice_stt_provider="stub",
        voice_tts_provider="stub",
        voice_vad_provider="manual",
        voice_wakeword_provider="stub",
        voice_microphone_provider="stub",
        voice_audio_output_provider="stub",
    )


@pytest.mark.asyncio
async def test_voice_manager_process_audio_buffer(tmp_path: object) -> None:
    """Manager processes buffered audio through the full pipeline."""
    settings = _settings(tmp_path)
    chat_service = AsyncMock()
    chat_service.chat = AsyncMock(
        return_value=ChatResponse(
            message="At your service.",
            conversation_id="conv-2",
            model="test",
            provider="openrouter",
        ),
    )
    platform = build_voice_platform(settings, chat_service)
    stt = StubSpeechToText(transcript="open my project")
    tts = StubTextToSpeech(audio=b"spoken-reply")
    audio_output = StubAudioOutput()
    conversation = ConversationController(
        settings,
        chat_service,
        tts,
        VoiceEventBus(),
    )
    manager = VoiceManager(
        enabled=True,
        settings=settings,
        microphone=platform.microphone,
        wake_word=platform.wake_word,
        vad=platform.vad,
        stt=stt,
        conversation=conversation,
        audio_output=audio_output,
        event_bus=VoiceEventBus(),
        silence_timeout_ms=settings.voice_silence_timeout_ms,
    )

    await manager.process_audio_buffer(b"audio-bytes")

    assert audio_output.played == [b"spoken-reply"]
    assert conversation.conversation_id == "conv-2"


@pytest.mark.asyncio
async def test_voice_manager_start_and_stop(tmp_path: object) -> None:
    """Manager transitions through listening and stopped states."""
    settings = _settings(tmp_path)
    chat_service = AsyncMock()
    platform = build_voice_platform(settings, chat_service)

    await platform.manager.start()
    assert platform.manager.state == VoiceLifecycleState.LISTENING

    await platform.manager.stop()
    assert platform.manager.state == VoiceLifecycleState.STOPPED
