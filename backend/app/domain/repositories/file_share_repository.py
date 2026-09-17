from abc import abstractmethod
from uuid import UUID

from app.domain.models.file_share import FileShare
from app.domain.repositories.base import Repository


class FileShareRepository(Repository[FileShare]):
    @abstractmethod
    def get_active(
        self,
        file_id: UUID,
        grantee_id: UUID,
    ) -> FileShare | None:
        pass

    @abstractmethod
    def list_for_file(
        self,
        file_id: UUID,
        include_revoked: bool = True,
    ) -> list[FileShare]:
        pass

    @abstractmethod
    def list_received_for_user(
        self,
        grantee_id: UUID,
        include_revoked: bool = False,
    ) -> list[FileShare]:
        pass

    @abstractmethod
    def list_sent_by_user(
        self,
        owner_id: UUID,
        include_revoked: bool = True,
    ) -> list[FileShare]:
        pass
