"""Chat API desktop tool integration test."""

from __future__ import annotations

import json
from collections.abc import Generator

import httpx
import pytest
from fastapi.testclient import TestClient

from app.config.settings import Environment, Settings
from app.core.app import create_app
from app.tools.implementations.desktop_tools import FocusWindowTool, TypeTextTool
from tests.tools.desktop.mock_desktop import MockDesktopAutomation


def _settings(tmp_path: object) -> Settings:
    """Build OpenRouter testing settings."""
    return Settings(
        _env_file=None,
        app_env=Environment.TESTING,
        debug=True,
        log_dir=tmp_path / "logs",  # type: ignore[operator]
        data_dir=tmp_path / "data",  # type: ignore[operator]
        api_secret_key="test-secret-key",
        llm_provider="openrouter",
        openrouter_api_key="sk-or-test-key",
        openrouter_model="anthropic/claude-3.5-sonnet",
        openrouter_api_base="https://openrouter.ai/api/v1",
        tools_enabled=True,
        desktop_automation_enabled=True,
    )


@pytest.fixture
def desktop_chat_client(tmp_path: object) -> Generator[TestClient, None, None]:
    """Client with mocked OpenRouter desktop tool sequence."""
    call_count = {"value": 0}
    desktop = MockDesktopAutomation()

    def handler(request: httpx.Request) -> httpx.Response:
        call_count["value"] += 1
        if call_count["value"] == 1:
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
                                        "id": "call_focus",
                                        "type": "function",
                                        "function": {
                                            "name": "desktop_focus_window",
                                            "arguments": json.dumps(
                                                {"title": "Notepad"}
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
        if call_count["value"] == 2:
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
                                        "id": "call_type",
                                        "type": "function",
                                        "function": {
                                            "name": "desktop_type_text",
                                            "arguments": json.dumps({"text": "hello"}),
                                        },
                                    }
                                ],
                            },
                            "finish_reason": "tool_calls",
                        }
                    ]
                },
            )
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "content": "Typed hello in Notepad.",
                        },
                        "finish_reason": "stop",
                    }
                ]
            },
        )

    app = create_app(_settings(tmp_path))
    tools = app.state.container.tools
    for tool_id in (
        "desktop.focus_window",
        "desktop.type_text",
        "desktop.click",
        "desktop.screenshot_region",
    ):
        tools.registry.unregister(tool_id)
    tools.registry.register(FocusWindowTool(desktop))
    tools.registry.register(TypeTextTool(desktop))

    provider = app.state.container.brain.openrouter_provider
    assert provider is not None
    provider._http_client = httpx.AsyncClient(  # noqa: SLF001
        transport=httpx.MockTransport(handler),
    )

    with TestClient(app) as client:
        yield client


def test_chat_open_notepad_and_type_flow(desktop_chat_client: TestClient) -> None:
    """Chat can focus a window and type text through desktop tools."""
    response = desktop_chat_client.post(
        "/api/v1/chat",
        json={"message": "Open Notepad and type hello"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["message"] == "Typed hello in Notepad."
    assert len(payload["tools_used"]) == 2
    assert payload["tools_used"][0]["tool_id"] == "desktop.focus_window"
    assert payload["tools_used"][1]["tool_id"] == "desktop.type_text"
