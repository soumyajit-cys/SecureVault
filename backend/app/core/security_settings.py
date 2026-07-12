from app.core.config import (
    get_settings
)


settings = get_settings()


def validate_security_settings():

    if len(settings.SECRET_KEY) < 32:
        raise RuntimeError(
            "SECRET_KEY too short"
        )

    if settings.PASSWORD_MIN_LENGTH < 12:
        raise RuntimeError(
            "Password policy invalid"
        )