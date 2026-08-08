from datetime import datetime
from datetime import timezone
from uuid import UUID

from sqlalchemy import delete
from sqlalchemy import or_
from sqlalchemy import select

from app.domain.models.password_reset_token import PasswordResetToken
from app.infrastructure.repositories.base_repository import (
    SQLAlchemyRepository,
)


class SQLAlchemyPasswordResetTokenRepository(
    SQLAlchemyRepository[PasswordResetToken]
):
    model = PasswordResetToken

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
            delete(PasswordResetToken)
            .where(
                or_(
                    PasswordResetToken.used_at.is_not(None),
                    PasswordResetToken.expires_at
                    < datetime.now(timezone.utc),
                ),
                PasswordResetToken.created_at < cutoff,
            )
        )

        result = self.db.execute(stmt)

        self.db.flush()

        return result.rowcount or 0

    def get_by_token_hash(
        self,
        token_hash: str,
    ) -> PasswordResetToken | None:

        stmt = (
            select(PasswordResetToken)
            .where(
                PasswordResetToken.token_hash
                == token_hash
            )
        )

        return self.db.scalar(stmt)

    def find_active(
        self,
        user_id: UUID,
    ) -> PasswordResetToken | None:

        stmt = (
            select(PasswordResetToken)
            .where(
                PasswordResetToken.user_id
                == user_id,
                PasswordResetToken.used_at.is_(None),
                PasswordResetToken.expires_at
                > datetime.now(timezone.utc),
            )
            .order_by(
                PasswordResetToken.created_at.desc()
            )
            .limit(1)
        )

        return self.db.scalar(stmt)

    def revoke_pending_for_user(
        self,
        user_id: UUID,
    ) -> None:

        pending = (
            select(PasswordResetToken)
            .where(
                PasswordResetToken.user_id
                == user_id,
                PasswordResetToken.used_at.is_(None),
            )
        )

        for token in self.db.scalars(pending):
            token.used_at = datetime.now(timezone.utc)

        self.db.flush()
