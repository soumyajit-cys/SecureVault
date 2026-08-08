import re
import time
import uuid

from starlette.middleware.base import (
    BaseHTTPMiddleware,
)
from starlette.responses import (
    JSONResponse,
)
from starlette.types import (
    Message,
    Receive,
    Send,
    Scope,
)

from app.core.config import get_settings
from app.core.logging import get_logger
from app.core.metrics import (
    record_request,
)
from app.core.rate_limit_backend import (
    RateLimitBackend,
    build_rate_limit_backend,
)

logger = get_logger(__name__)

_instances: list["RateLimitMiddleware"] = []


class RequestIDMiddleware(
    BaseHTTPMiddleware
):
    """
    Attach a request ID header for distributed tracing.
    """

    HEADER = "X-Request-ID"
    KEY = "request_id"

    async def dispatch(
        self,
        request,
        call_next,
    ):

        request_id = (
            request.headers.get(
                self.HEADER
            )
            or uuid.uuid4().hex
        )

        request.state.request_id = (
            request_id
        )

        response = await call_next(
            request
        )

        response.headers[
            self.HEADER
        ] = request_id

        return response


class SecurityHeadersMiddleware(
    BaseHTTPMiddleware
):

    HEADERS = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "Referrer-Policy": (
            "strict-origin-when-cross-origin"
        ),
        "X-XSS-Protection": "1; mode=block",
        "Cross-Origin-Opener-Policy": (
            "same-origin"
        ),
        "Permissions-Policy": (
            "camera=(), microphone=(), "
            "geolocation=()"
        ),
    }

    async def dispatch(
        self,
        request,
        call_next,
    ):

        response = await call_next(
            request
        )

        for name, value in (
            self.HEADERS.items()
        ):
            if name not in (
                response.headers
            ):
                response.headers[name] = (
                    value
                )

        if request.url.scheme == "https":

            response.headers[
                "Strict-Transport-Security"
            ] = (
                "max-age=31536000; "
                "includeSubDomains"
            )

        return response

    def __call__(
        self,
        scope: Scope,
        receive: Receive,
        send: Send,
    ):
        return super().__call__(
            scope, receive, send
        )


class RequestLoggingMiddleware(
    BaseHTTPMiddleware
):

    async def dispatch(
        self,
        request,
        call_next,
    ):

        request_id = getattr(
            request.state,
            "request_id",
            "n/a",
        )

        started = time.perf_counter()

        try:

            response = await call_next(
                request
            )

        except Exception:

            elapsed_ms = (
                time.perf_counter()
                - started
            ) * 1000

            logger.error(
                "request_failed",
                request_id=request_id,
                method=request.method,
                path=request.url.path,
                elapsed_ms=(
                    f"{elapsed_ms:.2f}"
                ),
                **getattr(
                    request.state,
                    "actor",
                    {},
                ),
            )

            raise

        elapsed_ms = (
            time.perf_counter()
            - started
        ) * 1000

        record_request(
            request.method,
            request.url.path,
            response.status_code,
            elapsed_ms,
        )

        logger.info(
            "request_completed",
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            status=response.status_code,
            elapsed_ms=(
                f"{elapsed_ms:.2f}"
            ),
            **getattr(
                request.state,
                "actor",
                {},
            ),
        )

        return response


class RateLimitMiddleware(
    BaseHTTPMiddleware
):
    """
    Sliding-window rate limiter.

    - A general bucket per IP for mutating requests.
    - A stricter bucket per IP for authentication
      endpoints (login / MFA / password reset), an
      anti-brute-force layer on top of the per-account
      limiter in AuthService.
    """

    LOGIN_PATHS = {
        "/api/v1/auth/login",
        "/api/v1/auth/mfa/verify",
        "/api/v1/auth/password-reset/request",
        "/api/v1/auth/password-reset/confirm",
    }

    CRYPTO_PATHS = {
        "/api/v1/encryption/text/encrypt",
        "/api/v1/encryption/text/decrypt",
        "/api/v1/files/upload",
        "/api/v1/files/download",
    }

    def __init__(
        self,
        app,
        general_limit: int,
        login_limit: int,
        crypto_limit: int = 20,
        window_seconds: int = 60,
        backend: RateLimitBackend | None = None,
    ):

        super().__init__(app)

        self.general_limit = (
            general_limit
        )

        self.login_limit = (
            login_limit
        )

        self.crypto_limit = (
            crypto_limit
        )

        self.window_seconds = (
            window_seconds
        )

        self.backend = (
            backend or build_rate_limit_backend()
        )

        _instances.append(self)

    async def dispatch(
        self,
        request,
        call_next,
    ):

        client_ip = (
            self._client_ip(
                request
            )
        )

        is_mutating = (
            request.method
            in {
                "POST",
                "PUT",
                "PATCH",
                "DELETE",
            }
        )

        is_login_path = (
            request.url.path
            in self.LOGIN_PATHS
        )

        is_crypto_path = (
            request.url.path
            in self.CRYPTO_PATHS
        )

        bucket_key: str | None = None

        bucket_limit: int | None = None

        if (
            is_login_path
            and request.method == "POST"
        ):
            bucket_key = (
                f"auth:{client_ip}"
            )
            bucket_limit = self.login_limit

        elif (
            is_crypto_path
            and request.method == "POST"
        ):
            bucket_key = (
                f"crypto:{client_ip}"
            )
            bucket_limit = self.crypto_limit

        elif is_mutating:
            bucket_key = f"ip:{client_ip}"
            bucket_limit = self.general_limit

        if bucket_key is not None:

            allowed = (
                self.backend.allow(
                    bucket_key,
                    bucket_limit,
                    self.window_seconds,
                )
            )

            if not allowed:

                return JSONResponse(
                    status_code=429,
                    content={
                        "detail": (
                            "Rate limit exceeded. "
                            "Please slow down."
                        )
                    },
                    headers={
                        "Retry-After": str(
                            self.window_seconds
                        ),
                        "X-RateLimit-Limit": str(
                            bucket_limit
                        ),
                        "X-RateLimit-Remaining": "0",
                    },
                )

            response = await call_next(
                request
            )

            response.headers[
                "X-RateLimit-Limit"
            ] = str(bucket_limit)

            response.headers[
                "X-RateLimit-Remaining"
            ] = str(
                self.backend.remaining(
                    bucket_key,
                    bucket_limit,
                    self.window_seconds,
                )
            )

            return response

        return await call_next(
            request
        )

    def _client_ip(
        self,
        request,
    ) -> str:

        forward_for = (
            request.headers.get(
                "X-Forwarded-For"
            )
        )

        if forward_for:

            trusted = get_settings().TRUSTED_PROXY_COUNT

            hops = [
                h.strip()
                for h in forward_for.split(",")
            ]

            if len(hops) > trusted:
                return hops[
                    -trusted - 1
                ]

        return (
            request.client.host
            if request.client
            else "unknown"
        )

    @classmethod
    def reset_all(cls) -> None:
        """
        Reset the state of every live instance
        (used by the test suite for isolation).
        """

        for instance in _instances:
            instance.backend.clear_all()