import pyotp

from app.core.config import get_settings

settings = get_settings()


class TOTPService:
    """
    TOTP (RFC 6238) wrapper around pyotp, honouring the
    configured period, digits and verification window.
    """

    def generate_secret(self) -> str:
        return pyotp.random_base32()

    def provisioning_uri(
        self,
        email: str,
        secret: str,
    ) -> str:

        totp = self._totp(secret)

        return totp.provisioning_uri(
            name=email,
            issuer_name=settings.TOTP_ISSUER,
        )

    def verify(
        self,
        secret: str,
        code: str,
    ) -> bool:

        totp = self._totp(secret)

        return totp.verify(
            code,
            valid_window=settings.TOTP_WINDOW,
        )

    def _totp(
        self,
        secret: str,
    ) -> pyotp.TOTP:

        return pyotp.TOTP(
            secret,
            digits=settings.TOTP_DIGITS,
            interval=settings.TOTP_PERIOD_SECONDS,
        )
