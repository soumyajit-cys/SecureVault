import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    response = client.get("/api/v1/health")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "healthy"
    assert data["service"] == "SecureVault"

    assert data["environment"] in {
        "development",
        "production",
        "test",
    }


def test_liveness():

    response = client.get(
        "/api/v1/health/live"
    )

    assert response.status_code == 200

    assert (
        response.json()["status"]
        == "healthy"
    )


def test_readiness():

    response = client.get(
        "/api/v1/health/ready"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] in {
        "healthy",
        "degraded",
        "unhealthy",
    }

    names = [
        c["name"]
        for c in data["checks"]
    ]

    assert "database" in names


def test_readiness_reports_database_down(monkeypatch):

    import app.api.routes.health as health_mod

    from app.schemas.health import (
        ReadinessCheck,
    )

    async def _broken_check_database():
        return ReadinessCheck(
            name="database",
            status="down",
            detail="connection refused",
        )

    monkeypatch.setattr(
        health_mod,
        "_check_database",
        _broken_check_database,
    )

    response = client.get(
        "/api/v1/health/ready"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "unhealthy"


def test_security_headers_present():

    response = client.get(
        "/api/v1/health"
    )

    assert (
        response.headers.get(
            "X-Content-Type-Options"
        )
        == "nosniff"
    )

    assert (
        response.headers.get(
            "X-Frame-Options"
        )
        == "DENY"
    )

    assert (
        response.headers.get(
            "Referrer-Policy"
        )
        == (
            "strict-origin-when-cross-origin"
        )
    )

    assert (
        "X-XSS-Protection"
        in response.headers
    )


def test_request_id_header_is_set():

    response = client.get(
        "/api/v1/health"
    )

    assert (
        "X-Request-ID"
        in response.headers
    )

    assert len(
        response.headers[
            "X-Request-ID"
        ]
    ) == 32


def test_request_id_echoes_client_header():

    sent = "client-supplied-abc123"

    response = client.get(
        "/api/v1/health",
        headers={"X-Request-ID": sent},
    )

    assert (
        response.headers[
            "X-Request-ID"
        ]
        == sent
    )


def test_metrics_endpoint():

    response = client.get(
        "/api/v1/metrics"
    )

    assert response.status_code == 200

    body = response.text

    assert (
        "vault_requests_total"
        in body
    )

    assert (
        "secure_uptime_seconds"
        in body
    )


def test_metrics_content_type():

    response = client.get(
        "/api/v1/metrics"
    )

    assert (
        response.headers[
            "Content-Type"
        ].startswith(
            "text/plain"
        )
    )


def test_cors_preflight():

    response = client.options(
        "/api/v1/health",
        headers={
            "Origin": (
                "http://localhost:5173"
            ),
            "Access-Control-Request-Method": (
                "GET"
            ),
        },
    )

    assert response.status_code == 200

    assert (
        "access-control-allow-origin"
        in response.headers
    )