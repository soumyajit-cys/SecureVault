from __future__ import annotations

import uuid
from pathlib import Path
from typing import BinaryIO

from app.core.exceptions import NotFoundError
from app.domain.models.crypto_key import CryptoKey
from app.domain.models.stored_file import StoredFile
from app.domain.repositories.stored_file_repository import (
    StoredFileRepository,
)
from app.services.encryption.file_decryptor import (
    FileDecryptor,
)
from app.services.encryption.folder_decryptor import (
    FolderDecryptor,
)
from app.services.key_management_service import (
    KeyManagementService,
)
from app.services.storage.storage_service import (
    StorageService,
)


class DownloadService:
    """
    Downloads encrypted files from the storage layout.

    Support:

    - streaming decryption into a caller-provided stream
    - decryption to a local path (files and folders)
    - raw encrypted container download
    """

    def __init__(
        self,
        storage: StorageService,
        stored_files: StoredFileRepository,
        keys: KeyManagementService,
        file_decryptor: FileDecryptor | None = None,
        folder_decryptor: FolderDecryptor | None = None,
    ) -> None:

        self._storage = storage

        self._files = stored_files

        self._keys = keys

        self._file_decryptor = (
            file_decryptor or FileDecryptor()
        )

        self._folder_decryptor = (
            folder_decryptor or FolderDecryptor()
        )

    # -------------------------------------------------
    # Lookup
    # -------------------------------------------------

    def get_for_user(
        self,
        user_id: uuid.UUID,
        file_id: uuid.UUID,
    ) -> StoredFile:
        """
        Fetch an active stored file owned by the user.

        Raises:
            NotFoundError: no such file.
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

    def container_path(
        self,
        file: StoredFile,
    ) -> Path:
        """
        Absolute path of the encrypted container on disk.
        """

        return self._storage.resolve_path(
            file.storage_path
        )

    # -------------------------------------------------
    # Streaming Decryption
    # -------------------------------------------------

    def stream_decrypted(
        self,
        file: StoredFile,
        key: CryptoKey,
        output: BinaryIO,
    ) -> tuple[str, int]:
        """
        Stream-decrypt a stored file into the given output stream.

        Returns:
            (sha256, chunk_count) of the recovered plaintext.

        Raises:
            NotFoundError: container missing on disk.
        """

        container = self.container_path(
            file
        )

        if not container.is_file():
            raise NotFoundError(
                "Encrypted container missing on disk."
            )

        private_key = self._keys.unlock_private_key(
            key
        )

        return self._file_decryptor.decrypt_to_stream(
            container,
            private_key,
            output,
        )

    # -------------------------------------------------
    # Path Decryption
    # -------------------------------------------------

    def decrypt_to_path(
        self,
        file: StoredFile,
        key: CryptoKey,
        destination: str | Path | None = None,
    ) -> Path:
        """
        Decrypt a stored file to a local path.

        Defaults to a unique path inside the storage vault area.
        """

        container = self.container_path(
            file
        )

        if not container.is_file():
            raise NotFoundError(
                "Encrypted container missing on disk."
            )

        private_key = self._keys.unlock_private_key(
            key
        )

        destination = (
            Path(destination)
            if destination
            else (
                self._storage.vault_dir_for()
                / file.original_filename
            )
        )

        result = self._file_decryptor.decrypt_file(
            container,
            private_key,
            output_path=destination,
        )

        return result.decrypted_path

    # -------------------------------------------------
    # Folder Restoration
    # -------------------------------------------------

    def restore_folder(
        self,
        file: StoredFile,
        key: CryptoKey,
        destination: str | Path | None = None,
    ) -> Path:
        """
        Decrypt a stored folder container and restore its tree.

        Raises:
            NotFoundError: file is not a folder or container missing.
        """

        if not file.is_folder:
            raise NotFoundError(
                "Stored file is not a folder."
            )

        container = self.container_path(
            file
        )

        if not container.is_file():
            raise NotFoundError(
                "Encrypted container missing on disk."
            )

        private_key = self._keys.unlock_private_key(
            key
        )

        result = self._folder_decryptor.decrypt_folder(
            container,
            private_key,
            destination=destination,
        )

        return result.restored_folder
