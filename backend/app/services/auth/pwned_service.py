import hashlib
from typing import Mapping

import httpx

from app.core.config import get_settings
from app.core.logging import get_logger

from app.services.auth.password_policy import (
    PasswordPolicy,
)

logger = get_logger(__name__)

PWNEDPASSWORDS_API = (
    "https://api.pwnedpasswords.com/range/"
)

settings = get_settings()


class PwnedPasswordChecker:
    """
    k-anonymity check against the Have I Been Pwned
    Pwned Passwords range API. The full password never
    leaves this service; only the first 5 characters of
    its SHA-1 hash do.
    """

    def __init__(
        self,
        client: httpx.Client | None = None,
    ) -> None:

        self.client = (
            client
            or httpx.Client(
                timeout=(
                    settings.PWNED_TIMEOUT_SECONDS
                )
            )
        )

    def is_pwned(
        self,
        password: str,
    ) -> bool:
        """
        Returns True when the password has appeared in
        known breach data.
        """

        if not settings.PWNED_CHECK_ENABLED:
            return False

        digest = (
            hashlib.sha1(
                password.encode("utf-8")
            )
            .hexdigest()
            .upper()
        )

        prefix = digest[:5]
        suffix = digest[5:]

        try:

            response = (
                self.client.get(
                    PWNEDPASSWORDS_API
                    + prefix
                )
            )

            response.raise_for_status()

        except httpx.HTTPError as exc:
            logger.warning(
                "pwned_check_unavailable",
                error=str(exc),
            )

            return False

        suffixes = self._parse_suffixes(
            response.text
        )

        return suffix in suffixes

    def assert_not_pwned(
        self,
        password: str,
    ) -> None:
        """
        Raise WeakPasswordError when the password is
        found in breach data and policy says to block.
        """

        if (
            settings.PWNED_ON_BREACH == "block"
            and self.is_pwned(password)
        ):

            from app.core.exceptions import (
                PwnedPasswordError,
            )

            raise PwnedPasswordError(
                "This password has appeared in "
                "known data breaches and cannot be "
                "used. Please choose another."
            )

    @staticmethod
    def _parse_suffixes(
        body: str,
    ) -> set[str]:

        return {
            line.split(":")[0].strip()
            for line in body.splitlines()
            if line.strip()
        }

    @staticmethod
    def validate_password(
        password: str,
        pwned: Mapping | None = None,
    ):
        """
        Run the configured policy plus the optional
        pwned check and raise on violation.
        """

        from app.core.exceptions import (
            WeakPasswordError,
        )

        from app.schemas.password import (
            PasswordValidationResult,
        )

        if pwned is None:
            pwned = PwnedPasswordChecker()

        result: PasswordValidationResult = (
            PasswordPolicy.validate(password)
        )

        if not result.valid:
            raise WeakPasswordError(
                result.message
            )

        pwned.assert_not_pwned(password)
