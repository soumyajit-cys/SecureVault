from abc import ABC
from abc import abstractmethod

from app.schemas.user import (
    UserCreate,
    UserLogin,
)


class AuthService(ABC):

    @abstractmethod
    def register(
        self,
        payload: UserCreate,
    ):
        pass

    @abstractmethod
    def login(
        self,
        payload: UserLogin,
    ):
        pass

    @abstractmethod
    def logout(
        self,
        refresh_token: str,
    ):
        pass