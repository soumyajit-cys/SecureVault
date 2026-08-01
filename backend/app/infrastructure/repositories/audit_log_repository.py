from typing import TypeVar
from uuid import UUID

from sqlalchemy import func
from sqlalchemy import select

from app.domain.models.audit_log import AuditLog
from app.infrastructure.repositories.base_repository import (
    SQLAlchemyRepository,
)

T = TypeVar("T")


class SQLAlchemyAuditLogRepository(
    SQLAlchemyRepository[AuditLog]
):
    model = AuditLog

    def list_for_user(
        self,
        user_id: UUID,
        page: int = 1,
        page_size: int = 20,
        action: str | None = None,
    ) -> tuple[list[AuditLog], int]:
        """
        Paginated audit trail for a single user.
        """

        filters = [
            AuditLog.user_id == user_id,
        ]

        if action:
            filters.append(
                AuditLog.action == action
            )

        total = (
            self.db.scalar(
                select(func.count(AuditLog.id))
                .where(*filters)
            )
            or 0
        )

        stmt = (
            select(AuditLog)
            .where(*filters)
            .order_by(
                AuditLog.created_at.desc(),
                AuditLog.id.desc(),
            )
            .offset((page - 1) * page_size)
            .limit(page_size)
        )

        items = list(
            self.db.scalars(stmt).all()
        )

        return items, total

    def list_all(
        self,
        page: int = 1,
        page_size: int = 20,
        action: str | None = None,
        user_id: UUID | None = None,
    ) -> tuple[list[AuditLog], int]:
        """
        Paginated global audit trail (admin).
        """

        filters = []

        if action:
            filters.append(
                AuditLog.action == action
            )

        if user_id:
            filters.append(
                AuditLog.user_id == user_id
            )

        total = (
            self.db.scalar(
                select(func.count(AuditLog.id))
                .where(*filters)
            )
            or 0
        )

        stmt = (
            select(AuditLog)
            .where(*filters)
            .order_by(
                AuditLog.created_at.desc(),
                AuditLog.id.desc(),
            )
            .offset((page - 1) * page_size)
            .limit(page_size)
        )

        items = list(
            self.db.scalars(stmt).all()
        )

        return items, total
