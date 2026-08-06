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

logger = get_logger(__name__)


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
            duration_ms=(
                f"{elapsed_ms:.2f}"
            ),
        )

        return response


class RateLimitMiddleware(
    BaseHTTPMiddleware
):
    """
    Sliding-window in-memory rate limiter keyed by IP.
    """

    def __init__(
        self,
        app,
        general_limit: int,
        login_limit: int,
        window_seconds: int = 60,
    ):

        super().__init__(app)

        self.general_limit = (
            general_limit
        )

        self.login_limit = (
            login_limit
        )

        self.window_seconds = (
            window_seconds
        )

        self._requests: dict[
            str, list[float]
        ] = {}

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

        if (
            request.method
            in {
                "POST",
                "PUT",
                "PATCH",
                "DELETE",
            }
            and not self._allows(
                client_ip,
                limit=self.general_limit,
            )
        ):

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
                    )
                },
            )

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

    def _allows(
        self,
        key: str,
        limit: int,
    ) -> bool:

        now = time.monotonic()

        window_start = (
            now - self.window_seconds
        )

        hits = [
            ts
            for ts in self._requests.get(
                key, []
            )
            if ts > window_start
        ]

        if len(hits) >= limit:
            self._requests[key] = hits
            return False

        hits.append(now)

        self._requests[key] = hits

        return True

    def reset(self) -> None:
        """
        Drop all recorded request timestamps. Used by
        tests for isolation between scenarios.
        """

        self._requests.clear()