import time

import pytest

from app.core.rate_limit_backend import (
    LocalRateLimitBackend,
    RedisRateLimitBackend,
    reset_local_rate_limit_backends,
)
from app.services.auth.login_rate_limiter import (
    LoginRateLimiter,
)

from app.core.exceptions import (
    LoginRateLimitedError,
)


@pytest.fixture(autouse=True)
def _clean_limiter():
    yield
    reset_local_rate_limit_backends()


def test_local_backend_window():
    backend = LocalRateLimitBackend()

    assert backend.allow("k", 3, 60) is True
    assert backend.allow("k", 3, 60) is True
    assert backend.allow("k", 3, 60) is True
    assert backend.allow("k", 3, 60) is False

    assert backend.remaining("k", 3, 60) == 0

    assert backend.allow("other", 3, 60) is True


def test_local_backend_keys_are_independent():
    backend = LocalRateLimitBackend()

    for _ in range(5):
        backend.allow("a", 5, 60)

    assert backend.allow("b", 1, 60) is True


def test_redis_backend_window():
    import redis as redis_module

    client = redis_module.from_url(
        "redis://127.0.0.1:6379/15",
        socket_connect_timeout=2,
    )

    try:
        client.ping()
    except Exception as exc:
        pytest.skip(f"redis unavailable: {exc}")

    backend = RedisRateLimitBackend(
        client,
        key_prefix="test-rl",
    )

    backend.clear_all()

    try:

        assert backend.allow("k", 2, 60) is True
        assert backend.allow("k", 2, 60) is True
        assert backend.allow("k", 2, 60) is False
        assert backend.remaining("k", 2, 60) == 0

        # Different key unaffected.
        assert backend.allow("z", 2, 60) is True

    finally:

        backend.clear_all()


def test_login_rate_limiter_raises():
    limiter = LoginRateLimiter(
        key_prefix="test-login",
        max_attempts=3,
    )

    key = LoginRateLimiter.key(
        "1.2.3.4",
        "A@example.com",
    )

    limiter.check(key)
    limiter.check(key)

    with pytest.raises(
        LoginRateLimitedError
    ):
        limiter.check(key)
        limiter.check(key)


def test_login_rate_limiter_shared_redis_state():
    """
    Two limiter instances share the same backend, so
    limits hold across workers.
    """

    import redis as redis_module

    client = redis_module.from_url(
        "redis://127.0.0.1:6379/15",
        socket_connect_timeout=2,
    )

    try:
        client.ping()
    except Exception as exc:
        pytest.skip(f"redis unavailable: {exc}")

    backend = RedisRateLimitBackend(
        client,
        key_prefix="test-rl2",
    )

    backend.clear_all()

    first = LoginRateLimiter(
        backend=backend,
        key_prefix="test-login",
        max_attempts=2,
    )

    second = LoginRateLimiter(
        backend=backend,
        key_prefix="test-login",
        max_attempts=2,
    )

    key = LoginRateLimiter.key(
        "9.9.9.9",
        "shared@example.com",
    )

    try:

        first.check(key)
        second.check(key)

        with pytest.raises(
            LoginRateLimitedError
        ):
            first.check(key)

    finally:

        backend.clear_all()


# -------------------------------------------------
# Middleware-level bucket tests
# -------------------------------------------------


@pytest.fixture
def limiter_app():
    """
    Minimal app with the real middleware and
    deliberately small limits so buckets can be
    exhausted in a few requests.
    """

    from fastapi import FastAPI

    from app.core.middleware import RateLimitMiddleware

    mini = FastAPI()

    @mini.post("/api/v1/encryption/text/encrypt")
    def encrypt():
        return {"ok": True}

    @mini.post("/api/v1/encryption/text/decrypt")
    def decrypt():
        return {"ok": True}

    @mini.post("/api/v1/other")
    def other():
        return {"ok": True}

    mini.add_middleware(
        RateLimitMiddleware,
        general_limit=10,
        login_limit=2,
        crypto_limit=2,
    )

    from fastapi.testclient import TestClient

    with TestClient(mini) as client:
        yield client


def test_crypto_bucket_limits_encrypt(
    limiter_app,
):
    """
    Crypto endpoints share a dedicated per-IP bucket,
    independent from the general mutating bucket.
    """

    assert (
        limiter_app.post(
            "/api/v1/encryption/text/encrypt"
        ).status_code
        == 200
    )

    assert (
        limiter_app.post(
            "/api/v1/encryption/text/encrypt"
        ).status_code
        == 200
    )

    response = limiter_app.post(
        "/api/v1/encryption/text/encrypt"
    )

    assert response.status_code == 429

    assert (
        response.headers[
            "X-RateLimit-Limit"
        ]
        == "2"
    )

    # The general bucket was not consumed by the
    # crypto calls: other mutating paths still work.
    assert (
        limiter_app.post(
            "/api/v1/other"
        ).status_code
        == 200
    )


def test_crypto_bucket_is_path_scoped(
    limiter_app,
):
    """
    Each crypto path has its own bucket; hammering
    /decrypt does not throttle /encrypt.
    """

    for _ in range(4):
        limiter_app.post(
            "/api/v1/encryption/text/decrypt"
        )

    assert (
        limiter_app.post(
            "/api/v1/encryption/text/encrypt"
        ).status_code
        == 200
    )


def test_download_path_matches_crypto_bucket(
    limiter_app,
):
    """
    Streaming decryption endpoints (/{file_id}/download)
    fall under the crypto bucket via prefix match.
    """

    from fastapi import FastAPI

    from app.core.middleware import RateLimitMiddleware

    mini = FastAPI()

    @mini.get("/api/v1/files/abc123/download")
    def download():
        return {"ok": True}

    mini.add_middleware(
        RateLimitMiddleware,
        general_limit=10,
        login_limit=2,
        crypto_limit=1,
    )

    from fastapi.testclient import TestClient

    with TestClient(mini) as client:

        assert (
            client.get(
                "/api/v1/files/abc123/download"
            ).status_code
            == 200
        )

        assert (
            client.get(
                "/api/v1/files/abc123/download"
            ).status_code
            == 429
        )
