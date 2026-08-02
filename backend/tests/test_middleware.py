import time

import pytest
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.responses import PlainTextResponse
from starlette.routing import Route
from starlette.testclient import TestClient

from app.core.middleware import (
    RateLimitMiddleware,
    RequestIDMiddleware,
)


async def _ok(request):
    return PlainTextResponse("ok")


@pytest.fixture
def limited_client():

    app = Starlette(
        routes=[
            Route(
                "/ping",
                _ok,
            )
        ],
        middleware=[
            Middleware(
                RateLimitMiddleware,
                general_limit=3,
                login_limit=1,
                window_seconds=60,
            ),
        ],
    )

    app.router.routes.append(
        Route(
            "/ping",
            _ok,
            methods=["POST"],
        )
    )

    return TestClient(app)


def test_rate_limit_exhaustion(limited_client):

    for _ in range(3):
        response = limited_client.post(
            "/ping"
        )
        assert response.status_code == 200

    response = limited_client.post(
        "/ping"
    )

    assert response.status_code == 429

    assert (
        "Retry-After"
        in response.headers
    )


def test_rate_limit_allows_reads(limited_client):

    for _ in range(10):
        response = limited_client.get(
            "/ping"
        )
        assert response.status_code == 200


def test_rate_limit_resets_after_window(limited_client):

    from unittest import mock

    now = time.monotonic()

    for _ in range(3):
        limited_client.post("/ping")

    with mock.patch(
        "app.core.middleware.time.monotonic",
        return_value=now + 61,
    ):

        response = limited_client.post(
            "/ping"
        )

    assert response.status_code == 200


def test_rate_limit_isolation_from_trusted_proxy():
    """
    When a trusted proxy forwards X-Forwarded-For,
    the client IP is derived from that header and
    buckets are isolated per client IP.
    """

    app = Starlette(
        routes=[
            Route("/ping", _ok)
        ],
        middleware=[
            Middleware(
                RateLimitMiddleware,
                general_limit=2,
                login_limit=1,
                window_seconds=60,
            ),
        ],
    )

    app.router.routes.append(
        Route(
            "/ping",
            _ok,
            methods=["POST"],
        )
    )

    client = TestClient(app)

    headers = {
        "X-Forwarded-For": "203.0.113.7"
    }

    client.post("/ping", headers=headers)
    client.post("/ping", headers=headers)

    assert (
        client.post(
            "/ping",
            headers=headers,
        ).status_code
        == 429
    )

    different_ip = {
        "X-Forwarded-For": "203.0.113.9"
    }

    assert (
        client.post(
            "/ping",
            headers=different_ip,
        ).status_code
        == 200
    )


def test_request_id_middleware_sets_header():

    app = Starlette(
        routes=[
            Route("/ping", _ok)
        ],
        middleware=[
            Middleware(RequestIDMiddleware)
        ],
    )

    client = TestClient(app)

    response = client.get("/ping")

    assert "X-Request-ID" in response.headers


def test_request_id_echoes_supplied():

    app = Starlette(
        routes=[
            Route("/ping", _ok)
        ],
        middleware=[
            Middleware(RequestIDMiddleware)
        ],
    )

    client = TestClient(app)

    response = client.get(
        "/ping",
        headers={"X-Request-ID": "abc"},
    )

    assert (
        response.headers["X-Request-ID"]
        == "abc"
    )