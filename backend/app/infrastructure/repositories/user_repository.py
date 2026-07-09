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