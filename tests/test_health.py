"""Health endpoint tests."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_health_returns_ok(client: TestClient) -> None:
    """GET /health returns status ok."""
    response = client.get("/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["environment"] == "testing"
    assert "timestamp" in payload


def test_version_returns_application_metadata(client: TestClient) -> None:
    """GET /version returns name and version."""
    response = client.get("/version")
    assert response.status_code == 200
    payload = response.json()
    assert payload["name"] == "Jarvis OS"
    assert payload["version"] == "0.1.0"
    assert payload["environment"] == "testing"


def test_root_serves_web_ui(client: TestClient) -> None:
    """GET / serves the Jarvis web UI (HTML)."""
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "<html" in response.text.lower()
