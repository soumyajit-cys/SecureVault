"""
HttpOnly cookie transport for refresh tokens with
CSRF double-submit protection.

The refresh token is stored exclusively in an HttpOnly,
SameSite=Strict cookie so JavaScript never sees it. The
access token stays in browser memory. State-changing
cookie-authenticated endpoints (refresh, logout) require
an X-CSRF-Token header matching the CSRF cookie
(double-submit pattern).
"""

from fastapi import HTTPException
from starlette.requests import Request
from starlette.responses import Response

from app.core.config import get_settings

REFRESH_COOKIE_NAME = "sv_refresh"

CSRF_COOKIE_NAME = "sv_csrf"

CSRF_HEADER = "X-CSRF-Token"

_COOKIE_PATH = "/api/v1/auth"


class CsrfValidationError(HTTPException):

    def __init__(self):
        super().__init__(
            status_code=403,
            detail="CSRF validation failed",
        )


def _cookie_secure() -> bool:
    settings = get_settings()

    if settings.SECURE_COOKIES:
        return True

    return settings.APP_ENV == "production"


def attach_auth_cookies(
    response: Response,
    refresh_token: str,
    max_age_seconds: int,
    csrf_token: str,
) -> None:
    """
    Set the HttpOnly refresh cookie and the CSRF cookie.
    """

    secure = _cookie_secure()

    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=refresh_token,
        max_age=max_age_seconds,
        path=_COOKIE_PATH,
        httponly=True,
        secure=secure,
        samesite="strict",
    )

    response.set_cookie(
        key=CSRF_COOKIE_NAME,
        value=csrf_token,
        max_age=max_age_seconds,
        path=_COOKIE_PATH,
        httponly=False,
        secure=secure,
        samesite="strict",
    )


def clear_auth_cookies(
    response: Response,
) -> None:
    """
    Delete both auth cookies.
    """

    response.delete_cookie(
        REFRESH_COOKIE_NAME,
        path=_COOKIE_PATH,
    )

    response.delete_cookie(
        CSRF_COOKIE_NAME,
        path=_COOKIE_PATH,
    )


def read_refresh_token(
    request: Request,
) -> str | None:
    return request.cookies.get(
        REFRESH_COOKIE_NAME
    )


def require_valid_csrf(
    request: Request,
) -> None:
    """
    Double-submit validation: the X-CSRF-Token header must
    equal the CSRF cookie value. Raising is safe: same-site
    requests carry the cookie; cross-site attackers cannot
    read it (SameSite=Strict drops it on cross-site POSTs).
    """

    supplied = request.headers.get(
        CSRF_HEADER
    )

    cookie_value = request.cookies.get(
        CSRF_COOKIE_NAME
    )

    if (
        not supplied
        or not cookie_value
        or supplied != cookie_value
    ):
        raise CsrfValidationError()