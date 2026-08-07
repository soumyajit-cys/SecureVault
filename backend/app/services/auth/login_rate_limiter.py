from app.core.config import get_settings

from app.core.exceptions import (
    LoginRateLimitedError,
)

from app.core.rate_limit_backend import (
    RateLimitBackend,
    build_rate_limit_backend,
)

settings = get_settings()


class LoginRateLimiter:
    """
    Sliding-window limiter keyed by ``ip:email`` for
    login and MFA verification endpoints.

    State lives in the shared rate-limit backend
    (Redis in multi-worker deployments, in-memory
    otherwise), so the limiter works across workers
    and survives per-request service re-creation.
    """

    KEY_PREFIX = "login"

    def __init__(
        self,
        backend: RateLimitBackend | None = None,
        key_prefix: str = "login",
        max_attempts: int | None = None,
        window_seconds: int = 60,
    ) -> None:

        self.backend = (
            backend or build_rate_limit_backend()
        )

        self.key_prefix = key_prefix

        self.max_attempts = (
            max_attempts
            or settings.RATE_LIMIT_LOGIN_PER_MINUTE
        )

        self.window_seconds = window_seconds

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

        if not self.backend.allow(
            f"{self.key_prefix}:{key}",
            self.max_attempts,
            self.window_seconds,
        ):
            raise LoginRateLimitedError(
                "Too many attempts. "
                "Please try again later."
            )

    def clear(self) -> None:

        self.backend.clear_all()

    @staticmethod
    def key(
        client_ip: str | None,
        email: str,
    ) -> str:

        return f"{(client_ip or 'unknown')}:{email.lower()}"


_shared_limiter = LoginRateLimiter()


def get_login_rate_limiter() -> LoginRateLimiter:
    """
    Module-level singleton so limits survive across
    requests (AuthService itself is rebuilt per
    request by the DI container).
    """

    return _shared_limiter
