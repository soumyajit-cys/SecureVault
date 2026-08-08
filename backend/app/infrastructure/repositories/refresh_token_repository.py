from uuid import UUID

from app.domain.models.refresh_token import (
    RefreshToken,
)
from app.infrastructure.repositories.base_repository import (
    SQLAlchemyRepository,
)

from sqlalchemy import delete
from sqlalchemy import select


class SQLAlchemyRefreshTokenRepository(
    SQLAlchemyRepository[
        RefreshToken
    ]
):
    model = RefreshToken

    def get_by_token_hash(
        self,
        token_hash: str,
    ) -> RefreshToken | None:
        return (
            self.db.query(
                RefreshToken
            )
            .filter(
                RefreshToken.token_hash
                == token_hash
            )
            .first()
        )

    def get_by_family(
        self,
        family: str,
    ):

        stmt = (
            select(
                RefreshToken
            )
            .where(
                RefreshToken.token_family
                == family
            )
        )

        return (
            self.db.scalars(stmt)
            .all()
        )

    def revoke_family(
        self,
        family: str,
    ):

        tokens = (
            self.get_by_family(
                family
            )
        )

        for token in tokens:
            token.revoked = True

        self.db.flush()

    def purge_older_than(
        self,
        cutoff,
    ) -> int:
        """
        Delete revoked refresh tokens once they pass
        the retention window. Active (non-revoked)
        tokens are never touched.
        """

        stmt = (
            delete(RefreshToken)
            .where(
                RefreshToken.revoked.is_(True),
                RefreshToken.created_at < cutoff,
            )
        )

        result = self.db.execute(stmt)

        self.db.flush()

        return result.rowcount or 0

    def get_active_by_hash(
        self,
        token_hash: str,
    ):

        stmt = (
            select(
                RefreshToken
            )
            .where(
                RefreshToken.token_hash
                == token_hash,
                RefreshToken.revoked.is_(False),
            )
        )

        return self.db.scalar(
            stmt
        )

    def revoke_by_session_id(
        self,
        session_id: UUID,
    ) -> None:

        tokens = (
            self.db.query(
                RefreshToken
            )
            .filter(
                RefreshToken.session_id
                == session_id
            )
            .all()
        )

        for token in tokens:
            token.revoked = True

        self.db.flush()

    def purge_older_than(
        self,
        cutoff,
    ) -> int:
        """
        Delete revoked refresh tokens once they pass
        the retention window. Active (non-revoked)
        tokens are never touched.
        """

        stmt = (
            delete(RefreshToken)
            .where(
                RefreshToken.revoked.is_(True),
                RefreshToken.created_at < cutoff,
            )
        )

        result = self.db.execute(stmt)

        self.db.flush()

        return result.rowcount or 0

    def revoke_all_for_user(
        self,
        user_id: UUID,
    ) -> None:

        tokens = (
            self.db.query(
                RefreshToken
            )
            .filter(
                RefreshToken.user_id
                == user_id,
                RefreshToken.revoked.is_(False),
            )
            .all()
        )

        for token in tokens:
            token.revoked = True

        self.db.flush()

    def purge_older_than(
        self,
        cutoff,
    ) -> int:
        """
        Delete revoked refresh tokens once they pass
        the retention window. Active (non-revoked)
        tokens are never touched.
        """

        stmt = (
            delete(RefreshToken)
            .where(
                RefreshToken.revoked.is_(True),
                RefreshToken.created_at < cutoff,
            )
        )

        result = self.db.execute(stmt)

        self.db.flush()

        return result.rowcount or 0

    def revoke_all_except_session(
        self,
        user_id: UUID,
        session_id: str,
    ) -> None:
        """
        Revoke every active refresh token for the
        user except the one bound to ``session_id``.
        """

        tokens = (
            self.db.query(
                RefreshToken
            )
            .filter(
                RefreshToken.user_id
                == user_id,
                RefreshToken.session_id
                != session_id,
                RefreshToken.revoked.is_(False),
            )
            .all()
        )

        for token in tokens:
            token.revoked = True

        self.db.flush()

    def purge_older_than(
        self,
        cutoff,
    ) -> int:
        """
        Delete revoked refresh tokens once they pass
        the retention window. Active (non-revoked)
        tokens are never touched.
        """

        stmt = (
            delete(RefreshToken)
            .where(
                RefreshToken.revoked.is_(True),
                RefreshToken.created_at < cutoff,
            )
        )

        result = self.db.execute(stmt)

        self.db.flush()

        return result.rowcount or 0

