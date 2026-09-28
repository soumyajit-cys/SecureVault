import json
import logging
import os

from app.core.config import (
    get_settings
)


logger = logging.getLogger(
    __name__
)

settings = get_settings()

_PLACEHOLDER_SECRETS = {
    "change-me-to-a-long-random-string",
    "changeme",
    "secret",
    "your-secret-key-here",
}

_PLACEHOLDER_SECRETS = {
    "change-me-to-a-long-random-string",
    "changeme",
    "secret",
    "your-secret-key-here",
    "test-secret-key-not-for-production",
    "ci-only-secret-key-not-for-production",
}

_PLACEHOLDER_PREFIXES = (
    "change-me",
    "changeme",
    "CHANGEME",
)


def _is_placeholder(value: str | None) -> bool:
    """
    True for known placeholder/test secrets (case-insensitive
    exact match, or any CHANGEME/change-me prefix).
    """

    if not value:
        return False

    lowered = value.lower()

    if lowered in _PLACEHOLDER_SECRETS:
        return True

    return lowered.startswith(_PLACEHOLDER_PREFIXES)


_PLACEHOLDER_ADMIN_PASSWORDS = {
    "change-me-Str0ng!AdminPass",
    "dev-Admin-Str0ng!2026",
    "admin",
    "password",
}


def validate_database_settings() -> None:
    """
    Fail fast on an unusable DATABASE_URL — at startup, in every
    environment, before the first connection attempt.
    """

    url = settings.DATABASE_URL or ""

    if url.startswith("sqlite:"):
        # Local dev/test convenience only.
        return

    if url.startswith("postgresql://"):
        raise RuntimeError(
            "DATABASE_URL uses the bare 'postgresql://' scheme, but "
            "this app talks to Postgres through psycopg v3. Use "
            "'postgresql+psycopg://user:pass@host:5432/dbname' "
            "(e.g. your Neon pooled URL with that prefix)."
        )

    if not url.startswith("postgresql+psycopg://"):
        scheme = url.split("://", 1)[0] if "://" in url else url
        raise RuntimeError(
            f"DATABASE_URL has unsupported scheme {scheme!r}. "
            "Use 'postgresql+psycopg://' (psycopg v3) or 'sqlite:' "
            "for local development."
        )

    query = url.split("?", 1)[1] if "?" in url else ""

    params = {
        pair.split("=", 1)[0].lower()
        for pair in query.split("&")
        if "=" in pair
    }

    if "channel_binding" in params and "channel_binding=require" in (
        query.lower()
    ):
        raise RuntimeError(
            "DATABASE_URL sets channel_binding=require, which pooled "
            "connections (Neon pooler, PgBouncer) do not support — "
            "every connection would fail. Remove the parameter or use "
            "channel_binding=disable."
        )


def validate_redis_settings() -> None:
    """
    Fail fast when the redis rate-limit backend is selected but
    REDIS_URL is missing or points at the wrong thing — the two
    classic mistakes being the Postgres URL and the Upstash REST
    URL, neither of which redis.from_url() can use.
    """

    if (settings.RATE_LIMIT_BACKEND or "local").lower() != "redis":
        return

    url = settings.REDIS_URL or ""

    if not url:
        raise RuntimeError(
            "RATE_LIMIT_BACKEND='redis' but REDIS_URL is not set."
        )

    scheme = url.split("://", 1)[0].lower() if "://" in url else ""

    if scheme in ("redis", "rediss"):
        return

    if scheme.startswith("postgres"):
        raise RuntimeError(
            "REDIS_URL looks like a Postgres URL — that is your "
            "DATABASE_URL. REDIS_URL must be your Upstash Redis "
            "connection URL, e.g. "
            "'rediss://default:<password>@<host>:6379'."
        )

    if scheme in ("http", "https") and "upstash.io" in url:
        raise RuntimeError(
            "REDIS_URL is an Upstash REST URL (https://...upstash.io) — "
            "the rate limiter needs the Redis wire protocol, not the "
            "REST API. In the Upstash dashboard copy the Redis URL "
            "(rediss://default:<password>@<host>:6379)."
        )

    raise RuntimeError(
        f"REDIS_URL has unsupported scheme {scheme!r}. "
        "Use 'redis://' or 'rediss://' (TLS)."
    )


def validate_cors_settings() -> None:
    """
    Fail fast on a CORS_ALLOW_ORIGINS value the server cannot
    honor: unparsable input, non-URL entries, or a wildcard
    combined with credentials (browsers reject that combination,
    so every authenticated cross-origin call would fail).
    """

    raw = os.environ.get("CORS_ALLOW_ORIGINS")

    if raw is not None:
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise RuntimeError(
                "CORS_ALLOW_ORIGINS must be a JSON list of origins, "
                'e.g. CORS_ALLOW_ORIGINS=\'["https://vault.example.com"]\'. '
                f"Parse error: {exc.msg}."
            ) from exc

        if not isinstance(parsed, list):
            raise RuntimeError(
                "CORS_ALLOW_ORIGINS must be a JSON list of origins, "
                'e.g. CORS_ALLOW_ORIGINS=\'["https://vault.example.com"]\'.'
            )

    origins = settings.CORS_ALLOW_ORIGINS or []

    if "*" in origins and settings.CORS_ALLOW_CREDENTIALS:
        raise RuntimeError(
            'CORS_ALLOW_ORIGINS contains "*" while '
            "CORS_ALLOW_CREDENTIALS is true — browsers forbid "
            "wildcard origins with credentials, so authenticated "
            "cross-origin requests would all fail. List exact "
            "origins instead."
        )

    for origin in origins:
        if origin == "*":
            continue
        if not (
            origin.startswith("http://")
            or origin.startswith("https://")
        ):
            raise RuntimeError(
                f"CORS_ALLOW_ORIGINS entry {origin!r} is not an "
                "absolute http(s) origin (scheme + host, no path, "
                "no trailing slash)."
            )


def validate_storage_settings() -> None:
    """
    Fail fast when the object-storage backend is
    misconfigured — at startup, not on first upload.

    Called from the app lifespan in every environment
    (unlike the production-only guards below).
    """

    backend = (settings.STORAGE_BACKEND or "local").lower()

    if backend not in ("local", "s3"):
        raise RuntimeError(
            "STORAGE_BACKEND must be 'local' or 's3', "
            f"got {settings.STORAGE_BACKEND!r}."
        )

    if backend != "s3":
        return

    missing = [
        name
        for name, value in (
            ("S3_ENDPOINT_URL", settings.S3_ENDPOINT_URL),
            ("S3_BUCKET", settings.S3_BUCKET),
            ("S3_ACCESS_KEY", settings.S3_ACCESS_KEY),
            ("S3_SECRET_KEY", settings.S3_SECRET_KEY),
        )
        if not value
    ]

    if missing:
        raise RuntimeError(
            "STORAGE_BACKEND='s3' but required settings "
            f"are missing: {', '.join(missing)}. "
            "Set them before starting the server."
        )


def validate_security_settings():

    if len(settings.SECRET_KEY) < 32:
        raise RuntimeError(
            "SECRET_KEY too short"
        )

    if settings.PASSWORD_MIN_LENGTH < 12:
        raise RuntimeError(
            "Password policy invalid"
        )

    if settings.APP_ENV == "development":
        return

    # Production guards. These raise so a misconfigured
    # deployment fails loudly at startup instead of
    # silently shipping with known-bad credentials.
    if _is_placeholder(settings.SECRET_KEY):
        raise RuntimeError(
            "SECRET_KEY is still set to a placeholder "
            "value from .env.example. Generate a real "
            "random secret before deploying."
        )

    admin_password = settings.VAULT_ADMIN_PASSWORD

    if admin_password and _is_placeholder(admin_password):
        raise RuntimeError(
            "VAULT_ADMIN_PASSWORD is still set to a "
            "placeholder value. Set a real password "
            "before deploying."
        )

    if (
        admin_password
        and len(admin_password) < settings.PASSWORD_MIN_LENGTH
    ):
        raise RuntimeError(
            "VAULT_ADMIN_PASSWORD must satisfy the password "
            "policy (at least "
            f"{settings.PASSWORD_MIN_LENGTH} characters)."
        )

    if settings.RATE_LIMIT_BACKEND != "redis":
        raise RuntimeError(
            "RATE_LIMIT_BACKEND must be 'redis' in "
            "production so rate-limit state is shared "
            "across instances."
        )

    if not settings.PWNED_CHECK_ENABLED:
        logger.warning(
            "PWNED_CHECK_ENABLED is disabled in "
            "production. Breached-password screening "
            "recommends PWNED_CHECK_ENABLED=true."
        )