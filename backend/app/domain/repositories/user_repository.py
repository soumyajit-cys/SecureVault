from abc import abstractmethod

from app.domain.models.user import User
from app.domain.repositories.base import Repository


class UserRepository(Repository[User]):

    @abstractmethod
    def get_by_email(self, email: str) -> User | None:
        pass

    @abstractmethod
    def get_by_username(self, username: str) -> User | None:
        pass


    