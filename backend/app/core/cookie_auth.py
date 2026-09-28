"""
HttpOnly cookie transport for refresh tokens with
CSRF double-submit protection.

The refresh token is stored exclusively in an HttpOnly
cookie so JavaScript never sees it. The access token stays
in browser memory. State-changing cookie-authenticated
endpoints (refresh, logout) require an X-CSRF-Token header
matching the CSRF cookie (double-submit pattern).

Cross-origin note (Vercel frontend -> Render backend): the
CSRF cookie is HttpOnly=False but frontend JS on another
origin still cannot read it via document.cookie, so every
token-issuing response ALSO carries `csrf_token` in its JSON
body and GET /auth/csrf re-issues the current value to a
holder of the refresh cookie. The client keeps it in memory
(exactly like the access token) and sends it back as the
X-CSRF-Token header. The server always validates header ==
cookie, so the double-submit property is unchanged.
"""

from fastapi import HTTPException
from starlette.requests import Request
from starlette.responses import Response

from app.core.config import get_settings

REFRESH_COOKIE_NAME = "sv_refresh"

CSRF_COOKIE_NAME = "sv_csrf"

CSRF_HEADER = "X-CSRF-Token"

_COOKIE_PATH = "/api/v1/auth"

# The CSRF cookie must be readable by client-side JS
# (double-submit), so it is scoped to the whole site.
_CSRF_PATH = "/"


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


def _cookie_samesite() -> str:
    """
    SameSite attribute, config-driven. Production forces
    "none": the frontend lives on another origin and browsers
    withhold Strict/Lax cookies on cross-site subrequests,
    which would silently break refresh/logout. "none" requires
    Secure, which production also forces (see _cookie_secure).
    """

    settings = get_settings()

    if settings.APP_ENV == "production":
        return "none"

    value = (settings.COOKIE_SAMESITE or "strict").lower()

    if value not in ("strict", "lax", "none"):
        raise RuntimeError(
            "COOKIE_SAMESITE must be 'strict', 'lax' or 'none', "
            f"got {settings.COOKIE_SAMESITE!r}."
        )

    return value


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

    samesite = _cookie_samesite()

    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=refresh_token,
        max_age=max_age_seconds,
        path=_COOKIE_PATH,
        httponly=True,
        secure=secure,
        samesite=samesite,
    )

    response.set_cookie(
        key=CSRF_COOKIE_NAME,
        value=csrf_token,
        max_age=max_age_seconds,
        path=_CSRF_PATH,
        httponly=False,
        secure=secure,
        samesite=samesite,
    )


def clear_auth_cookies(
    response: Response,
) -> None:
    """
    Delete both auth cookies. Attributes mirror the set call
    so browsers match the cookies to clear.
    """

    secure = _cookie_secure()

    samesite = _cookie_samesite()

    response.delete_cookie(
        REFRESH_COOKIE_NAME,
        path=_COOKIE_PATH,
        secure=secure,
        samesite=samesite,
    )

    response.delete_cookie(
        CSRF_COOKIE_NAME,
        path=_CSRF_PATH,
        secure=secure,
        samesite=samesite,
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
    equal the CSRF cookie value. The token is unguessable and
    readable only same-origin (cookie) or by an allowed CORS
    origin (response body); a cross-site attacker can trigger
    requests but can neither read the token nor forge the
    header, so forged requests fail here.
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