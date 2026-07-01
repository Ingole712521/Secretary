"""Multi-turn conversation API tests."""

from __future__ import annotations

import json
from collections.abc import Generator

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


@pytest.fixture
def conversation_client(tmp_path: object) -> Generator[TestClient, None, None]:
    """Return a test client that records LLM message history in mock responses."""
    captured_messages: list[dict[str, str]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content.decode())
        captured_messages.clear()
        captured_messages.extend(body["messages"])
        return httpx.Response(
            200,
            json={
                "id": "gen-multi",
                "model": "anthropic/claude-3.5-sonnet",
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "content": f"Turn {len(captured_messages)}",
                        },
                        "finish_reason": "stop",
                    }
                ],
                "usage": {
                    "prompt_tokens": 1,
                    "completion_tokens": 1,
                    "total_tokens": 2,
                },
            },
        )

    settings = _openrouter_settings(tmp_path)
    app = create_app(settings)
    provider = app.state.container.brain.openrouter_provider
    assert provider is not None
    provider._http_client = httpx.AsyncClient(  # noqa: SLF001
        transport=httpx.MockTransport(handler),
    )
    app.state.captured_messages = captured_messages  # type: ignore[attr-defined]

    with TestClient(app) as client:
        yield client


def test_multi_turn_chat_reuses_conversation_id(
    conversation_client: TestClient,
) -> None:
    """Follow-up messages use the same conversation_id and include history."""
    first = conversation_client.post(
        "/api/v1/chat",
        json={"message": "My name is Nehal"},
    )
    assert first.status_code == 200
    conversation_id = first.json()["conversation_id"]

    second = conversation_client.post(
        "/api/v1/chat",
        json={
            "message": "What is my name?",
            "conversation_id": conversation_id,
        },
    )
    assert second.status_code == 200
    assert second.json()["conversation_id"] == conversation_id

    captured = conversation_client.app.state.captured_messages
    roles = [message["role"] for message in captured]
    assert roles[0] == "system"
    assert roles.count("user") == 2
    assert roles.count("assistant") == 1
    assert any("Nehal" in message["content"] for message in captured)


def test_unknown_conversation_id_returns_404(
    conversation_client: TestClient,
) -> None:
    """Posting to an unknown conversation_id returns 404."""
    response = conversation_client.post(
        "/api/v1/chat",
        json={
            "message": "Hello",
            "conversation_id": "00000000-0000-0000-0000-000000000000",
        },
    )
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "CONVERSATION_NOT_FOUND"


def test_list_and_get_conversation(conversation_client: TestClient) -> None:
    """Conversation endpoints expose stored session history."""
    created = conversation_client.post(
        "/api/v1/chat",
        json={"message": "Remember this"},
    )
    conversation_id = created.json()["conversation_id"]

    listed = conversation_client.get("/api/v1/conversations")
    assert listed.status_code == 200
    summaries = listed.json()
    assert any(item["id"] == conversation_id for item in summaries)
    assert summaries[0]["message_count"] >= 2

    detail = conversation_client.get(f"/api/v1/conversations/{conversation_id}")
    assert detail.status_code == 200
    body = detail.json()
    assert body["id"] == conversation_id
    assert len(body["messages"]) == 2
    assert body["messages"][0]["role"] == "user"
    assert body["messages"][1]["role"] == "assistant"
