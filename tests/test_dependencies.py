"""Dependency injection tests."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.config.settings import Environment, Settings


def test_app_state_settings_match_test_fixture(
    client: TestClient,
    test_settings: Settings,
) -> None:
    """create_app stores the provided settings on app.state."""
    app_settings: Settings = client.app.state.settings
    assert app_settings.app_env == Environment.TESTING
    assert app_settings.app_env == test_settings.app_env


def test_service_container_uses_same_settings(client: TestClient) -> None:
    """Service container receives settings from app.state."""
    container_settings = client.app.state.container.settings
    app_settings = client.app.state.settings
    assert container_settings is app_settings


def test_service_container_includes_brain(client: TestClient) -> None:
    """Service container includes Brain subsystem after Sprint 2."""
    assert client.app.state.container.brain is not None
    assert client.app.state.container.brain.orchestrator is not None


def test_service_container_includes_tool_platform(client: TestClient) -> None:
    """Service container includes Tool platform after Sprint 3."""
    tools = client.app.state.container.tools
    assert tools is not None
    assert tools.registry is not None
    assert tools.executor is not None
    assert tools.registry.count() == 5
    assert tools.registry.find("terminal.run") is not None
    assert tools.registry.find("desktop.focus_window") is not None


def test_service_container_includes_chat_service(client: TestClient) -> None:
    """Service container includes ChatService for AI interactions."""
    chat_service = client.app.state.container.chat_service
    assert chat_service is not None


def test_service_container_includes_memory_service(client: TestClient) -> None:
    """Service container includes MemoryService after Sprint 7."""
    memory_service = client.app.state.container.memory_service
    assert memory_service is not None


def test_service_container_includes_voice_service(client: TestClient) -> None:
    """Service container includes VoiceService after Sprint 8."""
    voice_service = client.app.state.container.voice_service
    assert voice_service is not None
    assert voice_service.stt_provider_name == "stub"
    assert voice_service.tts_provider_name == "stub"
