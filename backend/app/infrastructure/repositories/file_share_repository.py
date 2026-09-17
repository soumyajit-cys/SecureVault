from uuid import UUID

from sqlalchemy import select

from app.domain.models.file_share import FileShare
from app.infrastructure.repositories.base_repository import (
    SQLAlchemyRepository,
)


class SQLAlchemyFileShareRepository(
    SQLAlchemyRepository[FileShare]
):
    model = FileShare

    def get_active(
        self,
        file_id: UUID,
        grantee_id: UUID,
    ) -> FileShare | None:
        stmt = (
            select(self.model)
            .where(
                self.model.file_id == file_id,
                self.model.grantee_id == grantee_id,
                self.model.revoked_at.is_(None),
            )
            .order_by(
                self.model.created_at.desc(),
            )
            .limit(1)
        )

        return self.db.scalar(stmt)

    def list_for_file(
        self,
        file_id: UUID,
        include_revoked: bool = True,
    ) -> list[FileShare]:
        stmt = select(self.model).where(
            self.model.file_id == file_id
        )

        if not include_revoked:
            stmt = stmt.where(
                self.model.revoked_at.is_(None)
            )

        stmt = stmt.order_by(
            self.model.created_at.desc()
        )

        return list(
            self.db.scalars(stmt).all()
        )

    def list_received_for_user(
        self,
        grantee_id: UUID,
        include_revoked: bool = False,
    ) -> list[FileShare]:
        stmt = select(self.model).where(
            self.model.grantee_id == grantee_id
        )

        if not include_revoked:
            stmt = stmt.where(
                self.model.revoked_at.is_(None)
            )

        stmt = stmt.order_by(
            self.model.created_at.desc()
        )

        return list(
            self.db.scalars(stmt).all()
        )

    def list_sent_by_user(
        self,
        owner_id: UUID,
        include_revoked: bool = True,
    ) -> list[FileShare]:
        stmt = select(self.model).where(
            self.model.owner_id == owner_id
        )

        if not include_revoked:
            stmt = stmt.where(
                self.model.revoked_at.is_(None)
            )

        stmt = stmt.order_by(
            self.model.created_at.desc()
        )

        return list(
            self.db.scalars(stmt).all()
        )
