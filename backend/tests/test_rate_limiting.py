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

        with pytest.raises(
            LoginRateLimitedError
        ):
            second.check(key)

    finally:

        backend.clear_all()
