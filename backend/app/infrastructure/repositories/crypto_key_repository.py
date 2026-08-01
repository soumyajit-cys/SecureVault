from datetime import datetime
from uuid import UUID

from sqlalchemy import func
from sqlalchemy import select
from sqlalchemy import update

from app.domain.models.crypto_key import CryptoKey
from app.infrastructure.repositories.base_repository import (
    SQLAlchemyRepository,
)


class SQLAlchemyCryptoKeyRepository(
    SQLAlchemyRepository[CryptoKey]
):
    model = CryptoKey

    def get_by_user_id(
        self,
        user_id: UUID,
        key_id: UUID,
    ) -> CryptoKey | None:

        stmt = (
            select(self.model)
            .where(
                self.model.id == key_id,
                self.model.user_id == user_id,
            )
        )

        return self.db.scalar(stmt)

    def list_by_user(
        self,
        user_id: UUID,
        status: str | None = None,
    ) -> list[CryptoKey]:

        stmt = (
            select(self.model)
            .where(
                self.model.user_id == user_id
            )
            .order_by(
                self.model.created_at.desc()
            )
        )

        if status:
            stmt = stmt.where(
                self.model.status == status
            )

        return list(
            self.db.scalars(stmt).all()
        )

    def get_active_for_user(
        self,
        user_id: UUID,
    ) -> CryptoKey | None:

        stmt = (
            select(self.model)
            .where(
                self.model.user_id == user_id,
                self.model.status == "active",
            )
            .order_by(
                self.model.created_at.desc()
            )
            .limit(1)
        )

        return self.db.scalar(stmt)

    def get_by_fingerprint(
        self,
        fingerprint: str,
    ) -> CryptoKey | None:

        stmt = (
            select(self.model)
            .where(
                self.model.fingerprint == fingerprint
            )
        )

        return self.db.scalar(stmt)

    def get_expired_keys(
        self,
        before: datetime,
    ) -> list[CryptoKey]:

        stmt = (
            select(self.model)
            .where(
                self.model.status == "active",
                self.model.expires_at.is_not(None),
                self.model.expires_at < before,
            )
        )

        return list(
            self.db.scalars(stmt).all()
        )

    def count_by_user(
        self,
        user_id: UUID,
    ) -> int:

        stmt = (
            select(
                func.count(self.model.id)
            )
            .where(
                self.model.user_id == user_id
            )
        )

        return self.db.scalar(stmt) or 0

    def mark_expired(
        self,
        keys: list[CryptoKey],
    ) -> int:

        if not keys:
            return 0

        ids = [
            key.id
            for key in keys
        ]

        result = self.db.execute(
            update(self.model)
            .where(
                self.model.id.in_(ids)
            )
            .values(
                status="expired",
                updated_at=func.now(),
            )
        )

        self.db.flush()

        return result.rowcount
