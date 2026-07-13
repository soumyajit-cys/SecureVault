from abc import ABC
from abc import abstractmethod


class PasswordService(ABC):

    @abstractmethod
    def hash_password(
        self,
        password: str,
    ) -> str:
        raise NotImplementedError

    @abstractmethod
    def verify_password(
        self,
        password: str,
        password_hash: str,
    ) -> bool:
        raise NotImplementedError
    

    