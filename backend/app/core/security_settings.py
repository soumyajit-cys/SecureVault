import logging

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

_PLACEHOLDER_ADMIN_PASSWORDS = {
    "change-me-Str0ng!AdminPass",
    "dev-Admin-Str0ng!2026",
    "admin",
    "password",
}


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
    if settings.SECRET_KEY.lower() in (
        _PLACEHOLDER_SECRETS
    ):
        raise RuntimeError(
            "SECRET_KEY is still set to a placeholder "
            "value from .env.example. Generate a real "
            "random secret before deploying."
        )

    if (
        settings.VAULT_ADMIN_PASSWORD
        and settings.VAULT_ADMIN_PASSWORD
        in _PLACEHOLDER_ADMIN_PASSWORDS
    ):
        raise RuntimeError(
            "VAULT_ADMIN_PASSWORD is still set to a "
            "placeholder value. Set a real password "
            "before deploying."
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