from datetime import datetime
from datetime import timezone
from uuid import UUID

from sqlalchemy import delete
from sqlalchemy import or_
from sqlalchemy import select

from app.domain.models.email_verification_token import (
    EmailVerificationToken,
)
from app.infrastructure.repositories.base_repository import (
    SQLAlchemyRepository,
)


class SQLAlchemyEmailVerificationTokenRepository(
    SQLAlchemyRepository[EmailVerificationToken]
):
    model = EmailVerificationToken

    def purge_older_than(
        self,
        cutoff,
    ) -> int:
        """
        Delete one-time tokens that are spent (used)
        or expired, once they pass the retention
        window.
        """

        stmt = (
            delete(EmailVerificationToken)
            .where(
                or_(
                    EmailVerificationToken.used_at.is_not(None),
                    EmailVerificationToken.expires_at
                    < datetime.now(timezone.utc),
                ),
                EmailVerificationToken.created_at < cutoff,
            )
        )

        result = self.db.execute(stmt)

        self.db.flush()

        return result.rowcount or 0

    def get_by_token_hash(
        self,
        token_hash: str,
    ) -> EmailVerificationToken | None:

        stmt = (
            select(EmailVerificationToken)
            .where(
                EmailVerificationToken.token_hash
                == token_hash
            )
        )

        return self.db.scalar(stmt)

    def revoke_pending_for_user(
        self,
        user_id: UUID,
    ) -> None:

        pending = (
            select(EmailVerificationToken)
            .where(
                EmailVerificationToken.user_id
                == user_id,
                EmailVerificationToken.used_at.is_(None),
            )
        )

        for token in self.db.scalars(pending):
            token.used_at = datetime.now(timezone.utc)

        self.db.flush()
