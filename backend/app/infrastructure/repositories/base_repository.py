from typing import Generic
from typing import TypeVar
from uuid import UUID

from sqlalchemy.orm import Session

T = TypeVar("T")


class SQLAlchemyRepository(
    Generic[T]
):
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
        return (
            self.db.query(self.model)
            .filter(
                self.model.id == entity_id
            )
            .first()
        )

    def create(
        self,
        entity: T,
    ) -> T:
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def update(
        self,
        entity: T,
    ) -> T:
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def delete(
        self,
        entity: T,
    ) -> None:
        self.db.delete(entity)
        self.db.commit()