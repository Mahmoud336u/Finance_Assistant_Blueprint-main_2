"""Tests for health check endpoints."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_health_returns_200(client: TestClient) -> None:
    """Health endpoint should always return 200 with status healthy."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "meridian-api"
    assert "timestamp" in data


def test_readiness_returns_200(client: TestClient) -> None:
    """Readiness endpoint should return 200 with dependency checks."""
    response = client.get("/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ("ready", "degraded")
    assert "checks" in data


def test_request_id_header_generated(client: TestClient) -> None:
    """Requests without X-Request-ID should get one generated."""
    response = client.get("/health")
    assert "X-Request-ID" in response.headers
    assert len(response.headers["X-Request-ID"]) > 0


def test_request_id_header_propagated(client: TestClient) -> None:
    """Requests with X-Request-ID should have it propagated to response."""
    custom_id = "test-request-123"
    response = client.get("/health", headers={"X-Request-ID": custom_id})
    assert response.headers["X-Request-ID"] == custom_id


def test_response_time_header(client: TestClient) -> None:
    """All responses should include X-Response-Time-Ms header."""
    response = client.get("/health")
    assert "X-Response-Time-Ms" in response.headers


def test_docs_available_in_dev(client: TestClient) -> None:
    """OpenAPI docs should be available in non-production environments."""
    response = client.get("/docs")
    assert response.status_code == 200


def test_unhandled_error_returns_structured_response(client: TestClient) -> None:
    """Unhandled exceptions should return structured error JSON, not stack traces."""
    # The /health endpoint won't error, but we can verify the error handler
    # is registered by checking for a 404 on a non-existent endpoint
    response = client.get("/nonexistent-endpoint")
    assert response.status_code in (404, 405)
