from app.domain.models.role import Role
from app.infrastructure.repositories.base_repository import (
    SQLAlchemyRepository,
)


class SQLAlchemyRoleRepository(
    SQLAlchemyRepository[Role]
):
    model = Role

    def get_by_name(
        self,
        name: str,
    ) -> Role | None:
        return (
            self.db.query(Role)
            .filter(Role.name == name)
            .first()
        )