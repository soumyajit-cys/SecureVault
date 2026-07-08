from abc import ABC
from abc import abstractmethod
from typing import Generic
from typing import TypeVar
from uuid import UUID

T = TypeVar("T")


class Repository(ABC, Generic[T]):

    @abstractmethod
    def get(self, entity_id: UUID) -> T | None:
        pass

    @abstractmethod
    def create(self, entity: T) -> T:
        pass

    @abstractmethod
    def update(self, entity: T) -> T:
        pass

    @abstractmethod
    def delete(self, entity: T) -> None:
        pass