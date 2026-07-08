from abc import abstractmethod

from app.domain.models.permission import Permission
from app.domain.repositories.base import Repository


class PermissionRepository(Repository[Permission]):

    @abstractmethod
    def get_by_name(self, name: str) -> Permission | None:
        pass