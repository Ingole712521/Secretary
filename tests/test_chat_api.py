"""Chat API endpoint tests."""

from __future__ import annotations

from collections.abc import Callable, Generator

import httpx
import pytest
from fastapi.testclient import TestClient

from app.config.settings import Environment, Settings
from app.core.app import create_app


def _openrouter_settings(tmp_path: object, **overrides: object) -> Settings:
    """Build testing settings with OpenRouter credentials."""
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
            "id": "gen-456",
            "model": "anthropic/claude-3.5-sonnet",
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": "Jarvis online.",
                    },
                    "finish_reason": "stop",
                }
            ],
            "usage": {"prompt_tokens": 8, "completion_tokens": 4, "total_tokens": 12},
        },
    )


@pytest.fixture
def chat_client(
    tmp_path: object,
    monkeypatch: pytest.MonkeyPatch,
) -> Generator[TestClient, None, None]:
    """Return a test client with a mocked OpenRouter HTTP transport."""
    settings = _openrouter_settings(tmp_path)
    app = create_app(settings)

    provider = app.state.container.brain.openrouter_provider
    assert provider is not None
    provider._http_client = httpx.AsyncClient(  # noqa: SLF001
        transport=_mock_transport(_success_handler),
    )

    with TestClient(app) as client:
        yield client


def test_chat_endpoint_returns_assistant_message(chat_client: TestClient) -> None:
    """POST /api/v1/chat returns a structured assistant response."""
    response = chat_client.post(
        "/api/v1/chat",
        json={"message": "Hello Jarvis"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["message"] == "Jarvis online."
    assert payload["provider"] == "openrouter"
    assert payload["model"] == "anthropic/claude-3.5-sonnet"
    assert payload["finish_reason"] == "stop"
    assert payload["usage"]["total_tokens"] == 12


def test_chat_endpoint_validates_empty_message(chat_client: TestClient) -> None:
    """POST /api/v1/chat rejects empty messages."""
    response = chat_client.post("/api/v1/chat", json={"message": ""})

    assert response.status_code == 422
    body = response.json()
    assert body["error"]["code"] == "VALIDATION_ERROR"


def test_chat_endpoint_requires_llm_credentials(tmp_path: object) -> None:
    """POST /api/v1/chat returns 500 when no API key is configured."""
    settings = _openrouter_settings(
        tmp_path,
        openrouter_api_key=None,
        openai_api_key=None,
    )
    app = create_app(settings)

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/chat",
            json={"message": "Hello"},
        )

    assert response.status_code == 500
    body = response.json()
    assert body["error"]["code"] == "CONFIGURATION_ERROR"


def test_chat_endpoint_supports_system_prompt(chat_client: TestClient) -> None:
    """POST /api/v1/chat accepts an optional system prompt."""
    response = chat_client.post(
        "/api/v1/chat",
        json={
            "message": "Who are you?",
            "system_prompt": "You are Jarvis.",
        },
    )

    assert response.status_code == 200
    assert response.json()["message"] == "Jarvis online."
