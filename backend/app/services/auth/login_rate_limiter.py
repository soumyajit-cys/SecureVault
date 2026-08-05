import time
from collections import defaultdict

from app.core.config import get_settings

from app.core.exceptions import (
    LoginRateLimitedError,
)

settings = get_settings()


class LoginRateLimiter:
    """
    Sliding-window in-memory limiter keyed by
    ``ip:email`` for login and MFA verification
    endpoints.
    """

    def __init__(
        self,
        max_attempts: int | None = None,
        window_seconds: int = 60,
    ) -> None:

        self.max_attempts = (
            max_attempts
            or settings.RATE_LIMIT_LOGIN_PER_MINUTE
        )

        self.window_seconds = window_seconds

        self._hits: defaultdict[
            str, list[float]
        ] = defaultdict(list)

    def check(
        self,
        key: str,
    ) -> None:
        """
        Record an attempt and raise
        ``LoginRateLimitedError`` when the limit for
        the window is exceeded.
        """

        if not settings.RATE_LIMIT_ENABLED:
            return

        now = time.monotonic()

        window_start = (
            now - self.window_seconds
        )

        hits = [
            ts
            for ts in self._hits[key]
            if ts > window_start
        ]

        if len(hits) >= self.max_attempts:
            self._hits[key] = hits

            raise LoginRateLimitedError(
                "Too many login attempts. "
                "Please try again later."
            )

        hits.append(now)

        self._hits[key] = hits

    @staticmethod
    def key(
        client_ip: str | None,
        email: str,
    ) -> str:

        return f"{(client_ip or 'unknown')}:{email.lower()}"
