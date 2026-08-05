import secrets
from datetime import datetime
from datetime import timezone

from app.core.config import get_settings

from app.core.exceptions import (
    MfaVerificationFailedError,
)

from app.domain.constants.audit_events import (
    MFA_DISABLED,
    MFA_ENABLED,
)

from app.domain.models.mfa_recovery_code import (
    MfaRecoveryCode,
)

from app.domain.models.user import User

from app.infrastructure.repositories.mfa_recovery_code_repository import (
    SQLAlchemyMfaRecoveryCodeRepository,
)

from app.infrastructure.repositories.user_repository import (
    SQLAlchemyUserRepository,
)

from app.services.audit_service import (
    AuditService,
)

from app.services.auth.totp_service import (
    TOTPService,
)

settings = get_settings()

RECOVERY_CODE_ALPHABET = (
    "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
)


class MfaService:
    """
    TOTP enrollment and verification plus one-time
    recovery codes (stored hashed).
    """

    def __init__(
        self,
        user_repository: SQLAlchemyUserRepository,
        recovery_code_repository: (
            SQLAlchemyMfaRecoveryCodeRepository
        ),
        audit_repository,
        totp_service: TOTPService | None = None,
    ) -> None:

        self.users = user_repository

        self.recovery_codes = (
            recovery_code_repository
        )

        self.audit_service = (
            AuditService(audit_repository)
        )

        self.totp = (
            totp_service or TOTPService()
        )

    # -------------------------------------------------
    # Setup
    # -------------------------------------------------

    def start_setup(
        self,
        user: User,
    ) -> dict:

        secret = (
            self.totp.generate_secret()
        )

        return {
            "secret": secret,
            "otpauth_uri": (
                self.totp.provisioning_uri(
                    user.email,
                    secret,
                )
            ),
        }

    def confirm_setup(
        self,
        user: User,
        code: str,
        secret: str,
    ) -> dict:
        """
        Verify the provided code against the secret
        returned by ``start_setup``, then persist it
        and mint recovery codes.
        """

        if not self.totp.verify(
            secret,
            code,
        ):
            raise MfaVerificationFailedError(
                "Invalid verification code"
            )

        user.totp_secret = secret

        user.totp_enabled = True

        user.totp_enabled_at = (
            datetime.now(timezone.utc)
        )

        self.users.update(user)

        codes = (
            self._rotate_recovery_codes(user)
        )

        self.audit_service.log(
            user.id,
            MFA_ENABLED,
        )

        return {
            "recovery_codes": codes,
            "message": (
                "MFA enabled. Store these recovery "
                "codes somewhere safe; they are "
                "shown only once."
            ),
        }

    # -------------------------------------------------
    # Verification
    # -------------------------------------------------

    def verify_login_code(
        self,
        user: User,
        code: str,
    ) -> bool:
        """
        Verify a TOTP or recovery code during login.
        Recovery codes are single-use.
        """

        if self.totp.verify(
            user.totp_secret,
            code,
        ):
            return True

        return (
            self._consume_recovery_code(
                user,
                code,
            )
        )

    def verify_disable_code(
        self,
        user: User,
        code: str,
    ) -> bool:

        return self.totp.verify(
            user.totp_secret,
            code,
        ) or self._consume_recovery_code(
            user,
            code,
        )

    # -------------------------------------------------
    # Disable
    # -------------------------------------------------

    def disable(
        self,
        user: User,
        code: str,
    ) -> None:

        if not self.verify_disable_code(
            user,
            code,
        ):
            raise MfaVerificationFailedError(
                "Invalid MFA code"
            )

        user.totp_secret = None

        user.totp_enabled = False

        user.totp_enabled_at = None

        self.users.update(user)

        self.recovery_codes.delete_all_for_user(
            user.id
        )

        self.audit_service.log(
            user.id,
            MFA_DISABLED,
        )

    # -------------------------------------------------
    # Recovery codes
    # -------------------------------------------------

    def _rotate_recovery_codes(
        self,
        user: User,
    ) -> list[str]:

        self.recovery_codes.delete_all_for_user(
            user.id
        )

        raw_codes = [
            self._generate_code()
            for _ in range(
                settings.MFA_RECOVERY_CODE_COUNT
            )
        ]

        for raw in raw_codes:

            self.recovery_codes.create(
                MfaRecoveryCode(
                    code_hash=self._hash(raw),
                    user_id=user.id,
                )
            )

        return raw_codes

    def _consume_recovery_code(
        self,
        user: User,
        code: str,
    ) -> bool:

        found = (
            self.recovery_codes
            .find_unused_by_hash(
                user.id,
                self._hash(code),
            )
        )

        if not found:
            return False

        self.recovery_codes.mark_used(
            found
        )

        return True

    @staticmethod
    def _hash(code: str) -> str:

        import hashlib

        return hashlib.sha256(
            code.encode("utf-8")
        ).hexdigest()

    @classmethod
    def _generate_code(cls) -> str:
        """
        Format: XXXX-XXXX-XXXX (no ambiguous chars).
        """

        chars = "".join(
            secrets.choice(RECOVERY_CODE_ALPHABET)
            for _ in range(12)
        )

        return "-".join(
            [
                chars[0:4],
                chars[4:8],
                chars[8:12],
            ]
        )
