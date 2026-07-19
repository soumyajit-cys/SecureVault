from abc import ABC
from abc import abstractmethod


class HashEngine(ABC):

    @abstractmethod
    def digest(
        self,
        data: bytes,
    ) -> str:
        raise NotImplementedError