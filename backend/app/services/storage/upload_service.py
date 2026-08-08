from __future__ import annotations

import hashlib
import mimetypes
import uuid
from pathlib import Path
from typing import BinaryIO

from cryptography.hazmat.primitives.asymmetric.rsa import (
    RSAPublicKey,
)

from app.core.exceptions import (
    FileTooLargeError,
    NotFoundError,
)

from app.crypto.file.file_header import FileHeader
from app.crypto.hashing.sha256 import SHA256Engine
from app.domain.models.crypto_key import CryptoKey
from app.domain.models.stored_file import StoredFile
from app.domain.repositories.stored_file_repository import (
    StoredFileRepository,
)
from app.services.encryption.file_encryptor import (
    FileEncryptor,
)
from app.services.encryption.folder_encryptor import (
    FolderEncryptor,
)
from app.services.key_management_service import (
    KeyManagementService,
)
from app.services.storage.quota_service import (
    QuotaService,
)
from app.services.storage.storage_service import (
    StorageService,
)


class UploadService:
    """
    Encrypts and stores files in the secure storage layout.

    Plaintext never touches the storage layout: content is streamed
    directly from the source into an encrypted container.

    Capabilities:

    - single file upload (streamed encryption)
    - folder upload (archive + encryption)
    - registration of pre-encrypted containers
    """

    def __init__(
        self,
        storage: StorageService,
        stored_files: StoredFileRepository,
        keys: KeyManagementService,
        file_encryptor: FileEncryptor | None = None,
        folder_encryptor: FolderEncryptor | None = None,
        quota_service: QuotaService | None = None,
    ) -> None:

        self._storage = storage

        self._files = stored_files

        self._keys = keys

        self._file_encryptor = (
            file_encryptor or FileEncryptor()
        )

        self._folder_encryptor = (
            folder_encryptor or FolderEncryptor()
        )

        self._quota_service = quota_service

        self._hasher = SHA256Engine()

    # -------------------------------------------------
    # File Upload
    # -------------------------------------------------

    def upload_file(
        self,
        user_id: uuid.UUID,
        key: CryptoKey,
        source: str | Path | BinaryIO,
        filename: str | None = None,
        mime_type: str | None = None,
        chunk_size: int = 4 * 1024 * 1024,
        quota_bytes: int | None = None,
        idempotency_key: str | None = None,
    ) -> StoredFile:
        """
        Stream-encrypt a file into the storage layout.

        Args:
            user_id: owning user.
            key: active encryption key used for key wrapping.
            source: path or open binary stream to encrypt.
            filename: original filename (required for streams).
            mime_type: optional MIME type; auto-detected otherwise.
            quota_bytes: per-user quota; None disables the check.
            idempotency_key: client-supplied replay key; the
                caller must deduplicate with
                ``find_idempotent`` before calling this.

        Raises:
            NotFoundError: source file does not exist.
            FileTooLargeError: source exceeds the maximum upload size.
            QuotaExceededError: storage quota would be exceeded.
        """

        public_key = self._public_key(key)

        name, size = self._inspect_source(
            source,
            filename,
        )

        if isinstance(source, (str, Path)):

            self._enforce_quota(
                user_id,
                quota_bytes,
                size,
            )

        file_id = uuid.uuid4()

        target = self._storage.container_path(
            user_id,
            file_id,
        )

        if isinstance(source, (str, Path)):

            result = self._file_encryptor.encrypt_file(
                source,
                public_key,
                output_path=target,
                chunk_size=chunk_size,
                owner_id=str(user_id),
            )

            original_size = size

        else:

            result, source_size = self._encrypt_stream_source(
                source,
                public_key,
                target,
                chunk_size,
                user_id,
            )

            if (
                source_size
                > self._max_upload_size()
            ):
                raise FileTooLargeError(
                    "Upload exceeds the maximum allowed size."
                )

            self._enforce_quota(
                user_id,
                quota_bytes,
                source_size,
            )

            original_size = source_size

        return self._register(
            user_id=user_id,
            key=key,
            file_id=file_id,
            filename=name,
            mime_type=(
                mime_type
                or mimetypes.guess_type(name)[0]
                or "application/octet-stream"
            ),
            original_size=original_size,
            encrypted_size=result.encrypted_size,
            sha256=result.sha256,
            is_folder=False,
            folder_file_count=0,
            container=target,
            idempotency_key=idempotency_key,
        )

    def find_idempotent(
        self,
        user_id: uuid.UUID,
        idempotency_key: str,
    ) -> StoredFile | None:
        """
        Return the stored file previously created with
        this idempotency key, if any.
        """

        if not idempotency_key:
            return None

        return (
            self._files.get_by_idempotency_key(
                user_id,
                idempotency_key,
            )
        )

    # -------------------------------------------------
    # Folder Upload
    # -------------------------------------------------

    def upload_folder(
        self,
        user_id: uuid.UUID,
        key: CryptoKey,
        folder_path: str | Path,
        quota_bytes: int | None = None,
    ) -> StoredFile:
        """
        Archive and encrypt an entire folder tree into storage.

        Raises:
            NotFoundError: folder does not exist.
            QuotaExceededError: storage quota would be exceeded.
        """

        folder = Path(folder_path)

        if not folder.is_dir():
            raise NotFoundError(
                f"Folder not found: {folder}"
            )

        public_key = self._public_key(key)

        file_id = uuid.uuid4()

        target = self._storage.container_path(
            user_id,
            file_id,
        )

        result = self._folder_encryptor.encrypt_folder(
            folder,
            public_key,
            output_path=target,
            owner_id=str(user_id),
        )

        self._enforce_quota(
            user_id,
            quota_bytes,
            result.archive_size,
        )

        file_count = result.file_count

        return self._register(
            user_id=user_id,
            key=key,
            file_id=file_id,
            filename=folder.name,
            mime_type="application/x-svlt-folder",
            original_size=result.archive_size,
            encrypted_size=result.encrypted_size,
            sha256=result.encryption.sha256,
            is_folder=True,
            folder_file_count=file_count,
            container=target,
        )

    # -------------------------------------------------
    # Pre-Encrypted Registration
    # -------------------------------------------------

    def register_container(
        self,
        user_id: uuid.UUID,
        key: CryptoKey,
        container_path: str | Path,
        filename: str,
        mime_type: str | None = None,
        is_folder: bool = False,
        folder_file_count: int = 0,
        quota_bytes: int | None = None,
    ) -> StoredFile:
        """
        Register an already-encrypted container (e.g. produced
        elsewhere) into the storage layout.
        """

        container = Path(container_path)

        if not container.is_file():
            raise NotFoundError(
                f"Container not found: {container}"
            )

        file_id = uuid.uuid4()

        target = self._storage.container_path(
            user_id,
            file_id,
        )

        size = container.stat().st_size

        self._enforce_quota(
            user_id,
            quota_bytes,
            size,
        )

        target.write_bytes(
            container.read_bytes()
        )

        return self._register(
            user_id=user_id,
            key=key,
            file_id=file_id,
            filename=filename,
            mime_type=(
                mime_type
                or "application/octet-stream"
            ),
            original_size=0,
            encrypted_size=size,
            sha256=self._hasher.digest_file(
                target
            ),
            is_folder=is_folder,
            folder_file_count=folder_file_count,
            container=target,
        )

    # -------------------------------------------------
    # Internals
    # -------------------------------------------------

    def _encrypt_stream_source(
        self,
        source: BinaryIO,
        public_key: RSAPublicKey,
        target: Path,
        chunk_size: int,
        user_id: uuid.UUID,
    ) -> tuple["EncryptionResult", int]:

        temp = self._storage.create_temp_path()

        source_size = 0

        try:

            with temp.open("wb") as out:

                while True:

                    chunk = source.read(chunk_size)

                    if not chunk:
                        break

                    source_size += len(chunk)

                    out.write(chunk)

            result = self._file_encryptor.encrypt_file(
                temp,
                public_key,
                output_path=target,
                chunk_size=chunk_size,
                owner_id=str(user_id),
            )

            return result, source_size

        finally:

            self._storage.remove(temp)

    def _register(
        self,
        user_id: uuid.UUID,
        key: CryptoKey,
        file_id: uuid.UUID,
        filename: str,
        mime_type: str,
        original_size: int,
        encrypted_size: int,
        sha256: str,
        is_folder: bool,
        folder_file_count: int,
        container: Path,
        idempotency_key: str | None = None,
    ) -> StoredFile:

        entity = StoredFile(
            id=file_id,
            user_id=user_id,
            key_id=key.id,
            original_filename=filename,
            storage_path=self._storage.relative_path(
                container
            ),
            mime_type=mime_type,
            original_size=original_size,
            encrypted_size=encrypted_size,
            sha256=sha256,
            is_folder=is_folder,
            folder_file_count=folder_file_count,
            status="active",
            idempotency_key=idempotency_key,
        )

        return self._files.create(entity)

    @staticmethod
    def _public_key(
        key: CryptoKey,
    ) -> RSAPublicKey:

        from app.crypto.rsa.rsa_service import RSAService

        return RSAService().load_public_key(
            key.public_key_pem.encode()
        )

    def _inspect_source(
        self,
        source: str | Path | BinaryIO,
        filename: str | None,
    ) -> tuple[str, int]:
        """
        Determine original name and size of the upload source.
        """

        if isinstance(
            source,
            (str, Path),
        ):

            path = Path(source)

            if not path.is_file():
                raise NotFoundError(
                    f"File not found: {path}"
                )

            if (
                path.stat().st_size
                > self._max_upload_size()
            ):
                raise FileTooLargeError(
                    "Upload exceeds the maximum allowed size."
                )

            return (
                filename or path.name,
                path.stat().st_size,
            )

        name = (
            filename
            or "upload.bin"
        )

        return name, 0

    def _enforce_quota(
        self,
        user_id: uuid.UUID,
        quota_bytes: int | None,
        additional_bytes: int,
    ) -> None:
        """
        Verify the new upload fits within the user's
        quota. No-op when quota is unset or no quota
        service is wired in.
        """

        if (
            quota_bytes is None
            or not self._quota_service
        ):
            return

        self._quota_service.check(
            user_id,
            quota_bytes,
            additional_bytes,
        )

    @staticmethod
    def _max_upload_size() -> int:

        from app.core.config import get_settings

        return (
            get_settings()
            .MAX_UPLOAD_SIZE_BYTES
        )
