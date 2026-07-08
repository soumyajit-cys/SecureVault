from abc import abstractmethod

from app.domain.models.role import Role
from app.domain.repositories.base import Repository


class RoleRepository(Repository[Role]):

    @abstractmethod
    def get_by_name(self, name: str) -> Role | None:
        pass