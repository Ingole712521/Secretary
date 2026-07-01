"""Basic API integration tests."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_correlation_id_header_is_present(client: TestClient) -> None:
    """Responses include a correlation ID header."""
    response = client.get("/health")
    assert response.status_code == 200
    assert "X-Correlation-ID" in response.headers
    assert len(response.headers["X-Correlation-ID"]) > 0


def test_correlation_id_header_is_propagated(client: TestClient) -> None:
    """Provided correlation ID is echoed in the response."""
    correlation_id = "test-correlation-id-12345"
    response = client.get(
        "/health",
        headers={"X-Correlation-ID": correlation_id},
    )
    assert response.status_code == 200
    assert response.headers["X-Correlation-ID"] == correlation_id


def test_openapi_docs_available_in_testing(client: TestClient) -> None:
    """OpenAPI documentation is available in non-production environments."""
    response = client.get("/docs")
    assert response.status_code == 200


def test_cors_headers_on_preflight(client: TestClient) -> None:
    """CORS preflight requests receive appropriate headers."""
    response = client.options(
        "/health",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.status_code == 200
    assert (
        response.headers.get("access-control-allow-origin") == "http://localhost:3000"
    )
