import time
from typing import Protocol

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class RateLimitBackend(Protocol):

    def allow(
        self,
        key: str,
        limit: int,
        window_seconds: int,
    ) -> bool:
        """Record an attempt; False when over the limit."""

    def remaining(
        self,
        key: str,
        limit: int,
        window_seconds: int,
    ) -> int:
        """Attempts still allowed in the current window."""

    def clear_all(self) -> None:
        """Drop all state (used by tests)."""


class LocalRateLimitBackend:
    """
    Sliding-window in-memory backend. Suitable for a
    single process; for multi-worker deployments use
    the Redis backend instead.
    """

    def __init__(self) -> None:

        self._requests: dict[
            str, list[float]
        ] = {}

        _local_instances.append(self)

    def allow(
        self,
        key: str,
        limit: int,
        window_seconds: int,
    ) -> bool:

        now = time.monotonic()

        window_start = now - window_seconds

        hits = [
            ts
            for ts in self._requests.get(key, [])
            if ts > window_start
        ]

        if len(hits) >= limit:
            self._requests[key] = hits
            return False

        hits.append(now)

        self._requests[key] = hits

        return True

    def remaining(
        self,
        key: str,
        limit: int,
        window_seconds: int,
    ) -> int:

        window_start = (
            time.monotonic() - window_seconds
        )

        hits = [
            ts
            for ts in self._requests.get(key, [])
            if ts > window_start
        ]

        return max(limit - len(hits), 0)

    def clear_all(self) -> None:

        self._requests.clear()


class RedisRateLimitBackend:
    """
    Sliding-window backend backed by a Redis sorted
    set (member = timestamp, score = timestamp).
    Shared across processes/workers.
    """

    def __init__(
        self,
        client,
        key_prefix: str = "rl",
    ) -> None:

        self.client = client

        self.prefix = key_prefix

    def _key(self, key: str) -> str:

        return f"{self.prefix}:{key}"

    def allow(
        self,
        key: str,
        limit: int,
        window_seconds: int,
    ) -> bool:

        now = time.time()

        redis_key = self._key(key)

        window_start = now - window_seconds

        pipeline = self.client.pipeline()

        pipeline.zremrangebyscore(
            redis_key,
            0,
            window_start,
        )

        pipeline.zcard(redis_key)

        pipeline.zadd(
            redis_key,
            {str(now): now},
        )

        pipeline.expire(
            redis_key,
            window_seconds * 2,
        )

        *_, count = pipeline.execute()

        if count >= limit:
            return False

        return True

    def remaining(
        self,
        key: str,
        limit: int,
        window_seconds: int,
    ) -> int:

        now = time.time()

        redis_key = self._key(key)

        count = (
            self.client.zcount(
                redis_key,
                now - window_seconds,
                now,
            )
        )

        return max(limit - count, 0)

    def clear_all(self) -> None:
        """
        Clear all rate-limit keys in this prefix.
        Intended for tests; use with care in prod.
        """

        cursor = 0

        while True:

            cursor, keys = (
                self.client.scan(
                    cursor,
                    match=f"{self.prefix}:*",
                    count=500,
                )
            )

            if keys:
                self.client.delete(*keys)

            if cursor == 0:
                break


_local_instances: list[LocalRateLimitBackend] = []


def _build_local_backend() -> LocalRateLimitBackend:
    """
    Reuse a single local backend per process so the
    login limiter and middleware share state and the
    test suite can reset it in one place.
    """

    for instance in _local_instances:
        return instance

    return LocalRateLimitBackend()


_local_default = _build_local_backend()

_cached_backend: RateLimitBackend | None = None


def build_rate_limit_backend() -> RateLimitBackend:
    """
    Build the configured backend once per process
    (subsequent calls return the cached instance).
    Falls back to the in-memory backend when Redis is
    configured but unreachable, so a Redis outage
    never turns into an auth outage.
    """

    global _cached_backend

    if _cached_backend is not None:
        return _cached_backend

    settings = get_settings()

    if (
        settings.RATE_LIMIT_BACKEND == "redis"
        and settings.REDIS_URL
    ):

        try:

            import redis as redis_module

            client = (
                redis_module.from_url(
                    settings.REDIS_URL,
                    socket_connect_timeout=1,
                    socket_timeout=1,
                )
            )

            client.ping()

            logger.info(
                "rate_limit_backend_redis",
                url=settings.REDIS_URL.split("@")[-1],
            )

            _cached_backend = (
                RedisRateLimitBackend(client)
            )

            return _cached_backend

        except Exception as exc:

            logger.warning(
                "rate_limit_backend_fallback_local",
                error=str(exc),
            )

    _cached_backend = _local_default

    return _cached_backend


def get_local_rate_limit_backend() -> LocalRateLimitBackend:
    """In-memory fallback shared across the process."""

    return _local_default


def reset_local_rate_limit_backends() -> None:
    """Test helper: clear every local backend."""

    for instance in _local_instances:
        instance.clear_all()
