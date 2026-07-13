import re

from app.core.config import (
    get_settings,
)

from app.schemas.password import (
    PasswordValidationResult,
)

settings = get_settings()


class PasswordPolicy:

    @staticmethod
    def validate(
        password: str,
    ) -> PasswordValidationResult:

        if len(password) < settings.PASSWORD_MIN_LENGTH:
            return PasswordValidationResult(
                valid=False,
                message=(
                    f"Password must contain "
                    f"at least "
                    f"{settings.PASSWORD_MIN_LENGTH} "
                    f"characters."
                ),
            )

        if (
            settings.PASSWORD_REQUIRE_UPPERCASE
            and not re.search(
                r"[A-Z]",
                password,
            )
        ):
            return PasswordValidationResult(
                valid=False,
                message=(
                    "Password must contain "
                    "at least one uppercase letter."
                ),
            )

        if (
            settings.PASSWORD_REQUIRE_LOWERCASE
            and not re.search(
                r"[a-z]",
                password,
            )
        ):
            return PasswordValidationResult(
                valid=False,
                message=(
                    "Password must contain "
                    "at least one lowercase letter."
                ),
            )

        if (
            settings.PASSWORD_REQUIRE_NUMBER
            and not re.search(
                r"\d",
                password,
            )
        ):
            return PasswordValidationResult(
                valid=False,
                message=(
                    "Password must contain "
                    "at least one number."
                ),
            )

        if (
            settings.PASSWORD_REQUIRE_SPECIAL
            and not re.search(
                r"[!@#$%^&*()_\-+=\[\]{};:,.<>?]",
                password,
            )
        ):
            return PasswordValidationResult(
                valid=False,
                message=(
                    "Password must contain "
                    "at least one special character."
                ),
            )

        return PasswordValidationResult(
            valid=True,
            message="Password accepted.",
        )