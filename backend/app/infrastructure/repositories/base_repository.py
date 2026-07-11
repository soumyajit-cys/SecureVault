from typing import Generic
from typing import TypeVar
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

T = TypeVar("T")


class SQLAlchemyRepository(Generic[T]):

    model = None

    def __init__(
        self,
        db: Session,
    ):
        self.db = db

    def get(
        self,
        entity_id: UUID,
    ) -> T | None:

        stmt = (
            select(self.model)
            .where(
                self.model.id == entity_id
            )
        )

        return self.db.scalar(stmt)

    def create(
        self,
        entity: T,
    ) -> T:

        self.db.add(entity)

        self.db.flush()

        self.db.refresh(entity)

        return entity

    def update(
        self,
        entity: T,
    ) -> T:

        self.db.flush()

        self.db.refresh(entity)

        return entity

    def delete(
        self,
        entity: T,
    ) -> None:

        self.db.delete(entity)

        self.db.flush()