from abc import abstractmethod
from datetime import datetime
from uuid import UUID

from app.domain.models.stored_file import StoredFile
from app.domain.repositories.base import Repository


class StoredFileRepository(Repository[StoredFile]):

    @abstractmethod
    def get_for_user(
        self,
        user_id: UUID,
        file_id: UUID,
        include_deleted: bool = False,
    ) -> StoredFile | None:
        pass

    @abstractmethod
    def list_for_user(
        self,
        user_id: UUID,
        page: int,
        page_size: int,
        status: str | None = None,
        mime_type: str | None = None,
        is_folder: bool | None = None,
        search: str | None = None,
    ) -> tuple[list[StoredFile], int]:
        pass

    @abstractmethod
    def get_by_storage_path(
        self,
        storage_path: str,
    ) -> StoredFile | None:
        pass

    @abstractmethod
    def get_deleted_before(
        self,
        before: datetime,
    ) -> list[StoredFile]:
        pass

    @abstractmethod
    def get_all_active(
        self,
    ) -> list[StoredFile]:
        pass

    @abstractmethod
    def soft_delete(
        self,
        file: StoredFile,
        deleted_at: datetime,
    ) -> StoredFile:
        pass

    @abstractmethod
    def count_active_for_user(
        self,
        user_id: UUID,
    ) -> int:
        pass
