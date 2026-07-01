"""Voice WebSocket API tests."""

from __future__ import annotations

import base64
from collections.abc import Callable, Generator

import httpx
import pytest
from fastapi.testclient import TestClient

from app.config.settings import Environment, Settings
from app.core.app import create_app


def _voice_client_settings(tmp_path: object, **overrides: object) -> Settings:
    """Build testing settings with stub voice and OpenRouter chat."""
    defaults: dict[str, object] = {
        "_env_file": None,
        "app_env": Environment.TESTING,
        "debug": True,
        "log_dir": tmp_path / "logs",  # type: ignore[operator]
        "data_dir": tmp_path / "data",  # type: ignore[operator]
        "api_secret_key": "test-secret-key",
        "llm_provider": "openrouter",
        "openrouter_api_key": "sk-or-test-key",
        "openrouter_model": "anthropic/claude-3.5-sonnet",
        "openrouter_api_base": "https://openrouter.ai/api/v1",
        "voice_enabled": True,
        "voice_stt_provider": "stub",
        "voice_tts_provider": "stub",
    }
    defaults.update(overrides)
    return Settings(**defaults)  # type: ignore[arg-type]


def _mock_transport(
    handler: Callable[[httpx.Request], httpx.Response],
) -> httpx.MockTransport:
    """Return a mock HTTP transport for OpenRouter requests."""
    return httpx.MockTransport(handler)


def _success_handler(_request: httpx.Request) -> httpx.Response:
    """Return a successful OpenRouter chat completion."""
    return httpx.Response(
        200,
        json={
            "id": "gen-voice",
            "model": "anthropic/claude-3.5-sonnet",
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": "At your service.",
                    },
                    "finish_reason": "stop",
                }
            ],
            "usage": {"prompt_tokens": 8, "completion_tokens": 4, "total_tokens": 12},
        },
    )


@pytest.fixture
def voice_client(
    tmp_path: object,
) -> Generator[TestClient, None, None]:
    """Return a test client with stub voice and mocked OpenRouter."""
    settings = _voice_client_settings(tmp_path)
    app = create_app(settings)

    provider = app.state.container.brain.openrouter_provider
    assert provider is not None
    provider._http_client = httpx.AsyncClient(  # noqa: SLF001
        transport=_mock_transport(_success_handler),
    )

    with TestClient(app) as client:
        yield client


def test_voice_websocket_full_turn(voice_client: TestClient) -> None:
    """WebSocket voice session returns transcript, reply, and audio."""
    with voice_client.websocket_connect("/api/v1/voice/ws") as ws:
        ready = ws.receive_json()
        assert ready["type"] == "ready"
        assert ready["voice_enabled"] is True
        assert ready["stt_provider"] == "stub"
        assert ready["tts_provider"] == "stub"

        ws.send_json({"type": "config", "conversation_id": None})
        ws.send_json(
            {
                "type": "audio",
                "data": base64.b64encode(b"fake-audio").decode("ascii"),
                "format": "wav",
            },
        )
        ws.send_json({"type": "end_turn"})

        transcript = ws.receive_json()
        assert transcript["type"] == "transcript"
        assert transcript["text"] == "hello jarvis"

        response = ws.receive_json()
        assert response["type"] == "response"
        assert response["text"] == "At your service."
        assert response["conversation_id"]

        audio_out = ws.receive_json()
        assert audio_out["type"] == "audio_out"
        assert audio_out["format"] == "mp3"
        assert base64.b64decode(audio_out["data"]) == b"fake-audio"


def test_voice_websocket_rejects_empty_audio(voice_client: TestClient) -> None:
    """end_turn without audio returns an error message."""
    with voice_client.websocket_connect("/api/v1/voice/ws") as ws:
        ws.receive_json()
        ws.send_json({"type": "end_turn"})
        error = ws.receive_json()
        assert error["type"] == "error"
        assert error["code"] == "NO_AUDIO"
