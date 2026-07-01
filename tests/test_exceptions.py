"""Exception handler tests."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.core.exception_mapping import resolve_status_code
from app.exceptions import (
    AuthenticationException,
    ConfigurationException,
    JarvisError,
    ValidationException,
)


def test_resolve_status_code_for_validation_exception() -> None:
    """ValidationException maps to HTTP 422."""
    assert resolve_status_code(ValidationException("invalid")) == 422


def test_resolve_status_code_for_auth_exception() -> None:
    """AuthenticationException maps to HTTP 401."""
    assert resolve_status_code(AuthenticationException("denied")) == 401


def test_resolve_status_code_for_base_jarvis_error() -> None:
    """Base JarvisError maps to HTTP 500."""
    assert resolve_status_code(JarvisError("failure", code="TEST")) == 500


def test_jarvis_error_returns_standard_envelope(client: TestClient) -> None:
    """JarvisError handler returns standardized error envelope."""

    @client.app.get("/test-error")
    def _raise_error() -> None:
        raise ValidationException("test validation failure")

    response = client.get("/test-error")
    assert response.status_code == 422
    payload = response.json()
    assert payload["error"]["code"] == "VALIDATION_ERROR"
    assert payload["error"]["message"] == "test validation failure"
    assert "correlation_id" in payload["error"]


def test_configuration_exception_maps_to_500() -> None:
    """ConfigurationException maps to HTTP 500."""
    assert resolve_status_code(ConfigurationException("bad config")) == 500
