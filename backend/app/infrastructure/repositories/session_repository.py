from datetime import datetime
from datetime import timezone
from uuid import UUID

from sqlalchemy import select

from app.domain.models.session import Session
from app.infrastructure.repositories.base_repository import (
    SQLAlchemyRepository,
)


class SQLAlchemySessionRepository(
    SQLAlchemyRepository[
        Session
    ]
):
    model = Session

    def list_for_user(
        self,
        user_id: UUID,
        include_revoked: bool = False,
    ) -> list[Session]:

        stmt = (
            select(self.model)
            .where(
                self.model.user_id == user_id
            )
            .order_by(
                self.model.created_at.desc()
            )
        )

        if not include_revoked:
            stmt = stmt.where(
                self.model.revoked.is_(False)
            )

        return list(
            self.db.scalars(stmt).all()
        )

    def get_for_user(
        self,
        user_id: UUID,
        session_id: UUID,
    ) -> Session | None:

        stmt = (
            select(self.model)
            .where(
                self.model.id == session_id,
                self.model.user_id == user_id,
            )
        )

        return self.db.scalar(stmt)

    def get_active_by_identifier(
        self,
        session_identifier: str,
    ) -> Session | None:

        stmt = (
            select(self.model)
            .where(
                self.model.session_identifier
                == session_identifier,
                self.model.revoked.is_(False),
                self.model.expires_at
                > datetime.now(timezone.utc),
            )
        )

        return self.db.scalar(stmt)

    def mark_seen(
        self,
        session: Session,
        at: datetime | None = None,
    ) -> Session:

        session.last_seen_at = (
            at or datetime.now(timezone.utc)
        )

        return self.update(session)
