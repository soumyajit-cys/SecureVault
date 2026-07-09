from app.domain.models.permission import Permission
from app.infrastructure.repositories.base_repository import (
    SQLAlchemyRepository,
)


class SQLAlchemyPermissionRepository(
    SQLAlchemyRepository[Permission]
):
    model = Permission

    def get_by_name(
        self,
        name: str,
    ) -> Permission | None:
        return (
            self.db.query(Permission)
            .filter(
                Permission.name == name
            )
            .first()
        )