from datetime import UTC
from datetime import datetime

from sqlalchemy import select

from app.domain.models.jwt_signing_key import JwtSigningKey
from app.infrastructure.repositories.base_repository import (
    SQLAlchemyRepository,
)


class SQLAlchemyJwtSigningKeyRepository(
    SQLAlchemyRepository
):

    model = JwtSigningKey

    def get_by_key_id(
        self,
        key_id: str,
    ) -> JwtSigningKey | None:

        stmt = (
            select(self.model)
            .where(
                self.model.key_id == key_id
            )
        )

        return self.db.scalar(stmt)

    def get_active(
        self,
    ) -> JwtSigningKey | None:

        stmt = (
            select(self.model)
            .where(
                self.model.status == "active"
            )
            .order_by(
                self.model.created_at.desc()
            )
        )

        return self.db.scalar(stmt)

    def list_all(
        self,
    ) -> list[JwtSigningKey]:

        stmt = (
            select(self.model)
            .order_by(
                self.model.created_at.asc()
            )
        )

        return list(
            self.db.scalars(stmt).all()
        )

    def retire(
        self,
        entry: JwtSigningKey,
        now: datetime,
    ) -> JwtSigningKey:

        entry.status = "retired"
        entry.retired_at = now

        return self.update(entry)