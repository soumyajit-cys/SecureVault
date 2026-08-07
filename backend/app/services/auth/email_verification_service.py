import secrets
from datetime import datetime
from datetime import timedelta
from datetime import timezone

from app.core.config import get_settings

from app.core.exceptions import (
    EmailVerificationTokenInvalidError,
)

from app.domain.constants.audit_events import (
    EMAIL_VERIFIED,
    VERIFICATION_SENT,
)

from app.domain.models.email_verification_token import (
    EmailVerificationToken,
)

from app.infrastructure.repositories.email_verification_token_repository import (
    SQLAlchemyEmailVerificationTokenRepository,
)

from app.services.audit_service import (
    AuditService,
)

from app.services.auth.email_service import (
    EmailService,
)

from app.services.auth.login_rate_limiter import (
    LoginRateLimiter,
)

settings = get_settings()


class EmailVerificationService:
    """
    One-time email verification tokens. Raw tokens
    are never persisted; only SHA-256 digests are.
    """

    TOKEN_EXPIRE_HOURS = (
        settings.EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS
    )

    def __init__(
        self,
        token_repository: (
            SQLAlchemyEmailVerificationTokenRepository
        ),
        audit_repository,
        email_service: EmailService | None = None,
    ) -> None:

        self.tokens = token_repository

        self.audit_service = (
            AuditService(audit_repository)
        )

        self.email_service = (
            email_service or EmailService()
        )

        self.issue_limiter = (
            LoginRateLimiter(
                key_prefix="verify:issue",
                max_attempts=5,
            )
        )

        self.confirm_limiter = (
            LoginRateLimiter(
                key_prefix="verify:confirm",
                max_attempts=10,
            )
        )

    def issue_for(
        self,
        user,
    ) -> str | None:
        """
        Create a fresh token, revoke outstanding
        ones, and email the link. Returns the raw
        token (used by tests); None when the user is
        already verified.
        """

        if user.is_verified:
            return None

        self.tokens.revoke_pending_for_user(
            user.id
        )

        raw_token = (
            secrets.token_urlsafe(32)
        )

        self.tokens.create(
            EmailVerificationToken(
                token_hash=self._hash(raw_token),
                expires_at=(
                    datetime.now(timezone.utc)
                    + timedelta(
                        hours=self.TOKEN_EXPIRE_HOURS
                    )
                ),
                user_id=user.id,
            )
        )

        verify_url = (
            f"{settings.APP_BASE_URL}/verify-email"
            f"?token={raw_token}"
        )

        self.email_service.send(
            to=user.email,
            subject=(
                "Verify your SecureVault email address"
            ),
            body=(
                "Welcome to SecureVault. Confirm "
                "your email address by opening the "
                "link below (valid for "
                f"{self.TOKEN_EXPIRE_HOURS} hours):\n\n"
                f"{verify_url}\n\n"
                "If you did not create this account, "
                "you can safely ignore this email."
            ),
        )

        self.audit_service.log(
            user.id,
            VERIFICATION_SENT,
        )

        return raw_token

    def verify(
        self,
        token: str,
    ) -> None:
        """
        Redeem the token and mark the account as
        verified. Raises on missing, used, expired or
        revoked tokens without revealing which.
        """

        token_hash = self._hash(token)

        record = (
            self.tokens.get_by_token_hash(
                token_hash
            )
        )

        if record and record.user:

            self.confirm_limiter.check(
                LoginRateLimiter.key(
                    None,
                    record.user.email,
                )
            )

        if not record or record.is_used:
            self._reject()

        if (
            self._as_utc(record.expires_at)
            < datetime.now(timezone.utc)
        ):
            self._reject()

        user = record.user

        if not user or not user.is_active:
            self._reject()

        user.is_verified = True

        self.tokens.revoke_pending_for_user(
            user.id
        )

        self.audit_service.log(
            user.id,
            EMAIL_VERIFIED,
        )

        return None

    @staticmethod
    def _reject() -> None:
        raise EmailVerificationTokenInvalidError(
            "Invalid or expired verification token"
        )

    @staticmethod
    def _hash(token: str) -> str:

        import hashlib

        return hashlib.sha256(
            token.encode("utf-8")
        ).hexdigest()

    @staticmethod
    def _as_utc(value: datetime) -> datetime:
        """
        SQLite returns naive datetimes; normalise to
        timezone-aware UTC for comparisons.
        """

        if value.tzinfo is None:
            return value.replace(
                tzinfo=timezone.utc
            )

        return value
