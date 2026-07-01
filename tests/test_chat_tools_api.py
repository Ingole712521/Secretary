"""Chat API tool-calling integration tests."""

from __future__ import annotations

import json
from collections.abc import Generator

import httpx
import pytest
from fastapi.testclient import TestClient

from app.config.settings import Environment, Settings
from app.core.app import create_app
from app.tools.implementations.terminal import TerminalTool


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
        "tools_enabled": True,
    }
    defaults.update(overrides)
    return Settings(**defaults)  # type: ignore[arg-type]


@pytest.fixture
def tool_chat_client(tmp_path: object) -> Generator[TestClient, None, None]:
    """Test client with mocked OpenRouter tool loop and terminal runner."""
    call_count = {"value": 0}

    async def runner(
        command: str,
        _cwd: str | None,
        _timeout_seconds: float,
    ) -> tuple[int, str, str]:
        return 0, f"output-for:{command}", ""

    def handler(request: httpx.Request) -> httpx.Response:
        call_count["value"] += 1
        body = json.loads(request.content.decode())
        if call_count["value"] == 1:
            assert body.get("tools")
            return httpx.Response(
                200,
                json={
                    "id": "gen-tools-1",
                    "model": "anthropic/claude-3.5-sonnet",
                    "choices": [
                        {
                            "message": {
                                "role": "assistant",
                                "content": "",
                                "tool_calls": [
                                    {
                                        "id": "call_terminal_1",
                                        "type": "function",
                                        "function": {
                                            "name": "terminal_run",
                                            "arguments": json.dumps(
                                                {
                                                    "command": (
                                                        "Get-ChildItem "
                                                        "$env:USERPROFILE\\Downloads"
                                                    )
                                                }
                                            ),
                                        },
                                    }
                                ],
                            },
                            "finish_reason": "tool_calls",
                        }
                    ],
                },
            )

        return httpx.Response(
            200,
            json={
                "id": "gen-tools-2",
                "model": "anthropic/claude-3.5-sonnet",
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "content": "Here are the files in Downloads.",
                        },
                        "finish_reason": "stop",
                    }
                ],
                "usage": {
                    "prompt_tokens": 20,
                    "completion_tokens": 10,
                    "total_tokens": 30,
                },
            },
        )

    settings = _openrouter_settings(tmp_path)
    app = create_app(settings)

    tools = app.state.container.tools
    tools.registry.unregister("terminal.run")
    tools.registry.register(TerminalTool(runner=runner))

    provider = app.state.container.brain.openrouter_provider
    assert provider is not None
    provider._http_client = httpx.AsyncClient(  # noqa: SLF001
        transport=httpx.MockTransport(handler),
    )

    with TestClient(app) as client:
        yield client


def test_chat_triggers_terminal_tool_and_returns_summary(
    tool_chat_client: TestClient,
) -> None:
    """POST /api/v1/chat runs terminal tool and returns tool metadata."""
    response = tool_chat_client.post(
        "/api/v1/chat",
        json={"message": "List files in my Downloads folder"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["message"] == "Here are the files in Downloads."
    assert len(payload["tools_used"]) == 1
    assert payload["tools_used"][0]["tool_id"] == "terminal.run"
    assert payload["tools_used"][0]["status"] == "success"
    assert "Downloads" in payload["tools_used"][0]["output"]["stdout"]


def test_chat_dangerous_command_requires_confirmation(tmp_path: object) -> None:
    """Dangerous commands return confirmation_required without executing."""
    settings = _openrouter_settings(tmp_path)
    app = create_app(settings)

    async def runner(
        _command: str,
        _cwd: str | None,
        _timeout_seconds: float,
    ) -> tuple[int, str, str]:
        raise AssertionError("runner should not be called")

    tools = app.state.container.tools
    tools.registry.unregister("terminal.run")
    tools.registry.register(TerminalTool(runner=runner))

    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "content": "",
                            "tool_calls": [
                                {
                                    "id": "call_danger",
                                    "type": "function",
                                    "function": {
                                        "name": "terminal_run",
                                        "arguments": json.dumps(
                                            {"command": "Remove-Item -Recurse temp"}
                                        ),
                                    },
                                }
                            ],
                        },
                        "finish_reason": "tool_calls",
                    }
                ]
            },
        )

    provider = app.state.container.brain.openrouter_provider
    assert provider is not None
    provider._http_client = httpx.AsyncClient(  # noqa: SLF001
        transport=httpx.MockTransport(handler),
    )

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/chat",
            json={"message": "Delete temp folder"},
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["confirmation_required"] is True
    assert payload["pending_tool_id"] == "terminal.run"
    assert payload["tools_used"] == []
