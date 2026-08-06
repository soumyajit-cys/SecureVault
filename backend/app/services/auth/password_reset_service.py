import secrets
from datetime import datetime
from datetime import timedelta
from datetime import timezone

from app.core.config import get_settings

from app.core.exceptions import (
    NotFoundError,
    PasswordResetTokenInvalidError,
)

from app.domain.constants.audit_events import (
    PASSWORD_RESET_COMPLETED,
    PASSWORD_RESET_REQUESTED,
)

from app.domain.models.password_reset_token import (
    PasswordResetToken,
)

from app.infrastructure.repositories.password_reset_token_repository import (
    SQLAlchemyPasswordResetTokenRepository,
)

from app.infrastructure.repositories.refresh_token_repository import (
    SQLAlchemyRefreshTokenRepository,
)

from app.infrastructure.repositories.session_repository import (
    SQLAlchemySessionRepository,
)

from app.infrastructure.repositories.user_repository import (
    SQLAlchemyUserRepository,
)

from app.services.audit_service import (
    AuditService,
)

from app.services.auth.email_service import (
    EmailService,
)

from app.services.auth.password_service import (
    Argon2PasswordService,
)

from app.services.auth.password_policy import (
    PasswordPolicy,
)

from app.services.auth.pwned_service import (
    PwnedPasswordChecker,
)

settings = get_settings()


class PasswordResetService:
    """
    One-time password reset tokens. Raw tokens are
    never persisted; only their SHA-256 digests are.
    """

    TOKEN_EXPIRE_MINUTES = 60

    def __init__(
        self,
        user_repository: SQLAlchemyUserRepository,
        token_repository: (
            SQLAlchemyPasswordResetTokenRepository
        ),
        session_repository: SQLAlchemySessionRepository,
        refresh_repository: (
            SQLAlchemyRefreshTokenRepository
        ),
        audit_repository,
        email_service: EmailService | None = None,
        pwned: PwnedPasswordChecker | None = None,
    ) -> None:

        self.users = user_repository

        self.tokens = token_repository

        self.sessions = session_repository

        self.refresh = refresh_repository

        self.audit_service = (
            AuditService(audit_repository)
        )

        self.email_service = (
            email_service or EmailService()
        )

        self.pwned = (
            pwned or PwnedPasswordChecker()
        )

        self.password_service = (
            Argon2PasswordService()
        )

    def request_reset(
        self,
        email: str,
    ) -> None:
        """
        Issue a reset token and email the link.
        Always returns silently for non-existent
        accounts to avoid user enumeration.
        """

        user = (
            self.users.get_by_email(email)
        )

        if not user:
            return None

        self.tokens.revoke_pending_for_user(
            user.id
        )

        raw_token = (
            secrets.token_urlsafe(32)
        )

        self.tokens.create(
            PasswordResetToken(
                token_hash=self._hash(raw_token),
                expires_at=(
                    datetime.now(timezone.utc)
                    + timedelta(
                        minutes=self.TOKEN_EXPIRE_MINUTES
                    )
                ),
                user_id=user.id,
            )
        )

        reset_url = (
            f"{settings.APP_BASE_URL}/reset-password"
            f"?token={raw_token}"
        )

        self.email_service.send(
            to=user.email,
            subject=(
                "Reset your SecureVault password"
            ),
            body=(
                "Someone requested a password reset "
                "for your SecureVault account.\n\n"
                "If this was you, open the link "
                "below (valid for 60 minutes):\n\n"
                f"{reset_url}\n\n"
                "If you did not request this, you "
                "can safely ignore this email."
            ),
        )

        self.audit_service.log(
            user.id,
            PASSWORD_RESET_REQUESTED,
        )

        return None

    def reset_password(
        self,
        token: str,
        new_password: str,
    ) -> None:
        """
        Validate the one-time token and set a new
        password, revoking all sessions and refresh
        tokens for the account.
        """

        token_hash = self._hash(token)

        record = (
            self.tokens.get_by_token_hash(
                token_hash
            )
        )

        if not record or record.is_used:
            raise PasswordResetTokenInvalidError(
                "Invalid or already used reset token"
            )

        if (
            self._as_utc(record.expires_at)
            < datetime.now(timezone.utc)
        ):
            raise PasswordResetTokenInvalidError(
                "Reset token has expired"
            )

        user = (
            self.users.get(record.user_id)
        )

        if not user or not user.is_active:
            raise PasswordResetTokenInvalidError(
                "Invalid reset token"
            )

        result = PasswordPolicy.validate(
            new_password
        )

        if not result.valid:

            from app.core.exceptions import (
                WeakPasswordError,
            )

            raise WeakPasswordError(
                result.message
            )

        self.pwned.assert_not_pwned(
            new_password
        )

        user.password_hash = (
            self.password_service
            .hash_password(
                new_password
            )
        )

        user.failed_login_attempts = 0

        user.locked_until = None

        self.users.update(user)

        record.used_at = (
            datetime.now(timezone.utc)
        )

        self.tokens.update(record)

        self.tokens.revoke_pending_for_user(
            user.id
        )

        self.refresh.revoke_all_for_user(
            user.id
        )

        for session in (
            self.sessions.list_for_user(
                user.id,
                include_revoked=True,
            )
        ):
            session.revoked = True
            self.sessions.update(session)

        self.audit_service.log(
            user.id,
            PASSWORD_RESET_COMPLETED,
        )

        return None

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
