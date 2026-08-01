from abc import abstractmethod
from datetime import datetime
from uuid import UUID

from app.domain.models.crypto_key import CryptoKey
from app.domain.repositories.base import Repository


class CryptoKeyRepository(Repository[CryptoKey]):

    @abstractmethod
    def get_by_user_id(
        self,
        user_id: UUID,
        key_id: UUID,
    ) -> CryptoKey | None:
        pass

    @abstractmethod
    def list_by_user(
        self,
        user_id: UUID,
        status: str | None = None,
    ) -> list[CryptoKey]:
        pass

    @abstractmethod
    def get_active_for_user(
        self,
        user_id: UUID,
    ) -> CryptoKey | None:
        pass

    @abstractmethod
    def get_by_fingerprint(
        self,
        fingerprint: str,
    ) -> CryptoKey | None:
        pass

    @abstractmethod
    def get_expired_keys(
        self,
        before: datetime,
    ) -> list[CryptoKey]:
        pass

    @abstractmethod
    def count_by_user(
        self,
        user_id: UUID,
    ) -> int:
        pass

    @abstractmethod
    def mark_expired(
        self,
        keys: list[CryptoKey],
    ) -> int:
        pass
