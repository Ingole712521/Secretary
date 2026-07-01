"""Memory API endpoint tests."""

from __future__ import annotations

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

from app.config.settings import Environment, Settings
from app.core.app import create_app


@pytest.fixture
def memory_client(tmp_path: object) -> Generator[TestClient, None, None]:
    """Return a test client with isolated memory database."""
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
    )
    app = create_app(settings)
    with TestClient(app) as client:
        yield client


def test_store_memory_fact(memory_client: TestClient) -> None:
    """POST /api/v1/memory stores a fact."""
    response = memory_client.post(
        "/api/v1/memory",
        json={"content": "User's name is Nehal", "tags": ["personal"]},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["content"] == "User's name is Nehal"
    assert payload["id"]


def test_search_memory_facts(memory_client: TestClient) -> None:
    """GET /api/v1/memory/search returns matching facts."""
    memory_client.post(
        "/api/v1/memory",
        json={"content": "User's name is Nehal"},
    )

    response = memory_client.get("/api/v1/memory/search", params={"q": "Nehal"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["query"] == "Nehal"
    assert len(payload["results"]) == 1
    assert "Nehal" in payload["results"][0]["content"]
