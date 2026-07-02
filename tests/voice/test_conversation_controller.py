"""Conversation controller tests."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from app.config.settings import Environment, Settings
from app.models.chat import ChatResponse
from app.voice.conversation.controller import ConversationController
from app.voice.events import VoiceEventBus
from app.voice.providers.tts.stub_tts import StubTextToSpeech


def _settings(tmp_path: object) -> Settings:
    return Settings(
        _env_file=None,
        app_env=Environment.TESTING,
        debug=True,
        log_dir=tmp_path / "logs",  # type: ignore[operator]
        data_dir=tmp_path / "data",  # type: ignore[operator]
        api_secret_key="test-secret-key",
    )


@pytest.mark.asyncio
async def test_conversation_controller_calls_chat_and_tts(tmp_path: object) -> None:
    """Controller forwards transcript to chat and synthesizes reply."""
    settings = _settings(tmp_path)
    chat_service = AsyncMock()
    chat_service.chat = AsyncMock(
        return_value=ChatResponse(
            message="Hello Nehal.",
            conversation_id="conv-1",
            model="test",
            provider="openrouter",
        ),
    )
    controller = ConversationController(
        settings,
        chat_service,
        StubTextToSpeech(audio=b"reply"),
        VoiceEventBus(),
    )

    turn = await controller.handle_transcript("hey jarvis")

    assert turn.transcript == "hey jarvis"
    assert turn.response_text == "Hello Nehal."
    assert turn.conversation_id == "conv-1"
    assert turn.synthesis.audio == b"reply"
