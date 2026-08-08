from __future__ import annotations

import uuid
from datetime import UTC, datetime

from app.core.exceptions import NotFoundError
from app.domain.models.stored_file import StoredFile
from app.domain.repositories.stored_file_repository import (
    StoredFileRepository,
)
from app.services.storage.storage_service import (
    StorageService,
)


class MetadataService:
    """
    Manages metadata of stored encrypted files.
    """

    def __init__(
        self,
        storage: StorageService,
        stored_files: StoredFileRepository,
    ) -> None:

        self._storage = storage

        self._files = stored_files

    # -------------------------------------------------
    # Reads
    # -------------------------------------------------

    def get(
        self,
        user_id: uuid.UUID,
        file_id: uuid.UUID,
    ) -> StoredFile:
        """
        Fetch an active stored file.

        Raises:
            NotFoundError: file does not exist.
        """

        file = self._files.get_for_user(
            user_id,
            file_id,
        )

        if file is None:
            raise NotFoundError(
                "Stored file not found."
            )

        return file

    def list(
        self,
        user_id: uuid.UUID,
        page: int = 1,
        page_size: int = 20,
        status: str | None = None,
        mime_type: str | None = None,
        is_folder: bool | None = None,
        search: str | None = None,
    ) -> tuple[list[StoredFile], int]:
        """
        Paginated, filterable listing of the user's files.

        Returns:
            (items, total_count)
        """

        page = max(page, 1)

        page_size = min(
            max(page_size, 1),
            100,
        )

        return self._files.list_for_user(
            user_id,
            page,
            page_size,
            status=status,
            mime_type=mime_type,
            is_folder=is_folder,
            search=search,
        )

    def storage_summary(
        self,
        user_id: uuid.UUID,
    ) -> dict:
        """
        Storage usage summary for a user.
        """

        files, total = self._files.list_for_user(
            user_id,
            1,
            100,
        )

        active_files = [
            f
            for f in files
            if f.is_active
        ]

        encrypted_bytes = sum(
            f.encrypted_size
            for f in active_files
        )

        original_bytes = sum(
            f.original_size
            for f in active_files
        )

        return {
            "file_count": total,
            "folder_count": sum(
                1
                for f in active_files
                if f.is_folder
            ),
            "encrypted_bytes": encrypted_bytes,
            "original_bytes": original_bytes,
        }

    # -------------------------------------------------
    # Updates
    # -------------------------------------------------

    def rename(
        self,
        user_id: uuid.UUID,
        file_id: uuid.UUID,
        new_name: str,
    ) -> StoredFile:
        """
        Rename a stored file.
        """

        file = self.get(
            user_id,
            file_id,
        )

        file.original_filename = (
            new_name.strip()
        )

        return self._files.update(file)

    def soft_delete(
        self,
        user_id: uuid.UUID,
        file_id: uuid.UUID,
    ) -> StoredFile:
        """
        Soft-delete a stored file.

        The encrypted container remains on disk until garbage
        collection purges it after the retention window.
        """

        file = self.get(
            user_id,
            file_id,
        )

        return self._files.soft_delete(
            file,
            datetime.now(UTC),
        )

    def purge(
        self,
        user_id: uuid.UUID,
        file_id: uuid.UUID,
    ) -> bool:
        """
        Immediately delete the record and its container on disk.

        Returns True when the file existed and was removed.
        """

        file = self._files.get_for_user(
            user_id,
            file_id,
            include_deleted=True,
        )

        if file is None:
            raise NotFoundError(
                "Stored file not found."
            )

        self._storage.remove_container(
            file
        )

        self._files.delete(file)

        return True
