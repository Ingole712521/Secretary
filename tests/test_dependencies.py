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
    assert tools.registry.count() == 0
