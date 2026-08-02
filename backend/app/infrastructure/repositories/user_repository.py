from app.domain.models.user import User
from app.infrastructure.repositories.base_repository import (
    SQLAlchemyRepository,
)


class SQLAlchemyUserRepository(
    SQLAlchemyRepository[User]
):
    model = User

    def get_by_email(
        self,
        email: str,
    ) -> User | None:
        return (
            self.db.query(User)
            .filter(User.email == email)
            .first()
        )

    def get_by_username(
        self,
        username: str,
    ) -> User | None:
        return (
            self.db.query(User)
            .filter(
                User.username == username
            )
            .first()
        )

    def list_all(
        self,
        page: int,
        page_size: int,
    ) -> tuple[list[User], int]:

        from sqlalchemy import func
        from sqlalchemy import select

        total = (
            self.db.scalar(
                select(func.count(User.id))
            )
            or 0
        )

        stmt = (
            select(User)
            .order_by(
                User.created_at.desc(),
                User.id.desc(),
            )
            .offset((page - 1) * page_size)
            .limit(page_size)
        )

        items = list(
            self.db.scalars(stmt).all()
        )

        return items, total