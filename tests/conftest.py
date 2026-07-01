"""Pytest configuration and shared fixtures."""

from __future__ import annotations

from collections.abc import Generator
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.config.settings import Environment, Settings, clear_settings_cache
from app.core.app import create_app


@pytest.fixture(autouse=True)
def _clear_settings_cache() -> Generator[None, None, None]:
    """Clear settings cache before and after each test."""
    clear_settings_cache()
    yield
    clear_settings_cache()


@pytest.fixture
def test_settings(tmp_path: Any) -> Settings:
    """Return settings configured for the testing environment."""
    return Settings(
        _env_file=None,
        app_env=Environment.TESTING,
        debug=True,
        log_dir=tmp_path / "logs",
        data_dir=tmp_path / "data",
        api_secret_key="test-secret-key",  # noqa: S106
        voice_stt_provider="stub",
        voice_tts_provider="stub",
    )


@pytest.fixture
def client(test_settings: Settings) -> Generator[TestClient, None, None]:
    """Return a FastAPI test client with testing settings."""
    app = create_app(test_settings)
    with TestClient(app) as test_client:
        yield test_client
