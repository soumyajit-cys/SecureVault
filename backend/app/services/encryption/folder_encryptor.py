from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.rsa import (
    RSAPublicKey,
)

from app.crypto.exceptions import EncryptionError
from app.services.encryption.file_encryptor import (
    FileEncryptor,
)

from app.services.encryption.folder_archiver import (
    ArchiveError,
    FolderArchiver,
)

from app.services.encryption.models.encryption_result import (
    EncryptionResult,
)


@dataclass(slots=True)
class FolderEncryptionResult:
    """
    Outcome of encrypting a folder tree.
    """

    source_folder: Path

    archive_path: Path

    encrypted_path: Path

    file_count: int

    directory_count: int

    archive_size: int

    encrypted_size: int

    encryption: EncryptionResult

    success: bool = True

    message: str = "Folder encrypted successfully."


class FolderEncryptor:
    """
    Compresses a folder tree and encrypts the resulting archive.

    The pipeline is fully streaming:

    1. ``FolderArchiver`` recursively traverses the folder and
       writes a compressed ZIP archive.
    2. ``FileEncryptor`` streams the archive into a SecureVault
       container, so memory usage stays flat for large folders.
    """

    def __init__(
        self,
        archiver: FolderArchiver | None = None,
        file_encryptor: FileEncryptor | None = None,
    ) -> None:

        self._archiver = (
            archiver or FolderArchiver()
        )

        self._file_encryptor = (
            file_encryptor or FileEncryptor()
        )

    def encrypt_folder(
        self,
        folder_path: str | Path,
        public_key: RSAPublicKey,
        output_path: str | Path | None = None,
        owner_id: str | None = None,
    ) -> FolderEncryptionResult:
        """
        Archive and encrypt an entire folder.

        Args:
            folder_path: directory tree to encrypt.
            public_key: RSA public key for key wrapping.
            output_path: optional destination container path.
                Defaults to ``<folder>.zip.svlt`` beside the folder.
            owner_id: optional owner identifier stored in metadata.

        Raises:
            EncryptionError: archiving or encryption failed.
        """

        folder = Path(folder_path)

        if not folder.is_dir():
            raise EncryptionError(
                f"Folder not found: {folder}"
            )

        archive = (
            folder.with_suffix(".zip")
        )

        output = (
            Path(output_path)
            if output_path
            else folder.with_suffix(".zip.svlt")
        )

        try:

            archive_path = self._archiver.create_archive(
                folder,
                archive,
            )

            result = self._file_encryptor.encrypt_file(
                archive_path,
                public_key,
                output_path=output,
                owner_id=owner_id,
            )

        except ArchiveError as exc:
            raise EncryptionError(
                f"Folder archiving failed: {exc}"
            ) from exc

        file_count = sum(
            1
            for path in folder.rglob("*")
            if path.is_file()
        )

        directory_count = sum(
            1
            for path in folder.rglob("*")
            if path.is_dir()
        )

        return FolderEncryptionResult(
            source_folder=folder,
            archive_path=archive_path,
            encrypted_path=result.encrypted_path,
            file_count=file_count,
            directory_count=directory_count,
            archive_size=archive_path.stat().st_size,
            encrypted_size=result.encrypted_size,
            encryption=result,
        )
