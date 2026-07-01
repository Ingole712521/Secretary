"""Chat memory injection tests."""

from __future__ import annotations

import json
from collections.abc import Generator

import httpx
import pytest
from fastapi.testclient import TestClient

from app.config.settings import Environment, Settings
from app.core.app import create_app


@pytest.fixture
def memory_chat_client(tmp_path: object) -> Generator[TestClient, None, None]:
    """Client with memory stored and mocked OpenRouter."""
    settings = Settings(
        _env_file=None,
        app_env=Environment.TESTING,
        debug=True,
        log_dir=tmp_path / "logs",
        data_dir=tmp_path / "data",
        memory_db_path=tmp_path / "memory.db",
        api_secret_key="test-secret-key",
        llm_provider="openrouter",
        openrouter_api_key="sk-or-test-key",
        openrouter_model="anthropic/claude-3.5-sonnet",
        openrouter_api_base="https://openrouter.ai/api/v1",
        tools_enabled=False,
    )
    app = create_app(settings)

    store_response = TestClient(app).post(
        "/api/v1/memory",
        json={"content": "User's name is Nehal", "tags": ["personal"]},
    )
    assert store_response.status_code == 200

    captured_messages: list[dict[str, str]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content.decode())
        captured_messages.clear()
        captured_messages.extend(body["messages"])
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "content": "Hello Nehal!",
                        },
                        "finish_reason": "stop",
                    }
                ]
            },
        )

    provider = app.state.container.brain.openrouter_provider
    assert provider is not None
    provider._http_client = httpx.AsyncClient(  # noqa: SLF001
        transport=httpx.MockTransport(handler),
    )
    app.state.captured_messages = captured_messages  # type: ignore[attr-defined]

    with TestClient(app) as client:
        yield client


def test_chat_injects_relevant_memories(memory_chat_client: TestClient) -> None:
    """Chat requests include relevant long-term memory in system messages."""
    response = memory_chat_client.post(
        "/api/v1/chat",
        json={"message": "What is my name?", "enable_tools": False},
    )

    assert response.status_code == 200
    captured = memory_chat_client.app.state.captured_messages
    memory_messages = [
        message["content"]
        for message in captured
        if message["role"] == "system" and "Known facts" in message["content"]
    ]
    assert memory_messages
    assert "Nehal" in memory_messages[0]
