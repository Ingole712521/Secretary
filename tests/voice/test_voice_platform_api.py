"""Voice platform REST API tests."""

from __future__ import annotations

from collections.abc import Callable, Generator

import httpx
import pytest
from fastapi.testclient import TestClient

from app.config.settings import Environment, Settings
from app.core.app import create_app


def _settings(tmp_path: object, **overrides: object) -> Settings:
    defaults: dict[str, object] = {
        "_env_file": None,
        "app_env": Environment.TESTING,
        "debug": True,
        "log_dir": tmp_path / "logs",  # type: ignore[operator]
        "data_dir": tmp_path / "data",  # type: ignore[operator]
        "api_secret_key": "test-secret-key",
        "llm_provider": "openrouter",
        "openrouter_api_key": "sk-or-test-key",
        "voice_stt_provider": "stub",
        "voice_tts_provider": "stub",
        "voice_vad_provider": "manual",
        "voice_wakeword_provider": "stub",
        "voice_microphone_provider": "stub",
        "voice_audio_output_provider": "stub",
    }
    defaults.update(overrides)
    return Settings(**defaults)  # type: ignore[arg-type]


def _mock_transport(
    handler: Callable[[httpx.Request], httpx.Response],
) -> httpx.MockTransport:
    return httpx.MockTransport(handler)


def _success_handler(_request: httpx.Request) -> httpx.Response:
    return httpx.Response(
        200,
        json={
            "id": "gen-voice",
            "model": "anthropic/claude-3.5-sonnet",
            "choices": [
                {
                    "message": {"role": "assistant", "content": "Ready."},
                    "finish_reason": "stop",
                }
            ],
            "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
        },
    )


@pytest.fixture
def platform_client(tmp_path: object) -> Generator[TestClient, None, None]:
    settings = _settings(tmp_path)
    app = create_app(settings)
    provider = app.state.container.brain.openrouter_provider
    assert provider is not None
    provider._http_client = httpx.AsyncClient(  # noqa: SLF001
        transport=_mock_transport(_success_handler),
    )
    with TestClient(app) as client:
        yield client


def test_voice_status_endpoint(platform_client: TestClient) -> None:
    """GET /api/v1/voice/status returns platform status."""
    response = platform_client.get("/api/v1/voice/status")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"]["enabled"] is True
    assert payload["status"]["state"] == "idle"


def test_voice_start_and_stop(platform_client: TestClient) -> None:
    """POST start/stop controls voice lifecycle."""
    start = platform_client.post("/api/v1/voice/start")
    assert start.status_code == 200
    assert start.json()["status"]["state"] == "listening"

    stop = platform_client.post("/api/v1/voice/stop")
    assert stop.status_code == 200
    assert stop.json()["status"]["state"] == "stopped"
