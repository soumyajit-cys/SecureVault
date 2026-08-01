from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.rsa import (
    RSAPrivateKey,
)

from app.crypto.exceptions import DecryptionError
from app.services.encryption.file_decryptor import (
    FileDecryptor,
)

from app.services.encryption.folder_archiver import (
    ArchiveError,
    FolderArchiver,
)

from app.services.encryption.models.decryption_result import (
    DecryptionResult,
)


@dataclass(slots=True)
class FolderDecryptionResult:
    """
    Outcome of decrypting a folder container.
    """

    source_path: Path

    archive_path: Path

    restored_folder: Path

    decryption: DecryptionResult

    restored_files: int = 0

    restored_directories: int = 0

    success: bool = True

    message: str = "Folder decrypted successfully."


class FolderDecryptor:
    """
    Decrypts a folder container and restores the folder structure.

    Pipeline:

    1. ``FileDecryptor`` streams the container back into the
       compressed archive (constant memory).
    2. ``FolderArchiver`` safely extracts the archive, restoring
       the original directory tree, rejecting any unsafe paths.
    """

    def __init__(
        self,
        archiver: FolderArchiver | None = None,
        file_decryptor: FileDecryptor | None = None,
    ) -> None:

        self._archiver = (
            archiver or FolderArchiver()
        )

        self._file_decryptor = (
            file_decryptor or FileDecryptor()
        )

    def decrypt_folder(
        self,
        source_path: str | Path,
        private_key: RSAPrivateKey,
        destination: str | Path | None = None,
        verify_integrity: bool = True,
    ) -> FolderDecryptionResult:
        """
        Decrypt a folder container and restore the directory tree.

        Args:
            source_path: encrypted ``.svlt`` folder container.
            private_key: RSA private key used to unwrap the session key.
            destination: optional restore directory.  Defaults to the
                parent directory of the container.
            verify_integrity: verify SHA-256 after decryption.

        Raises:
            DecryptionError: decryption or extraction failed.
        """

        source = Path(source_path)

        if not source.is_file():
            raise DecryptionError(
                f"Encrypted folder not found: {source}"
            )

        try:

            decryption = self._file_decryptor.decrypt_file(
                source,
                private_key,
                verify_integrity=verify_integrity,
            )

            archive_path = decryption.decrypted_path

            if not archive_path.is_file():
                raise ArchiveError(
                    "Decrypted payload is not an archive."
                )

            base = (
                Path(destination)
                if destination
                else source.parent
            )

            restored = self._archiver.extract_archive(
                archive_path,
                base,
            )

        except ArchiveError as exc:
            raise DecryptionError(
                f"Folder restoration failed: {exc}"
            ) from exc

        restored_files = sum(
            1
            for path in restored.rglob("*")
            if path.is_file()
        )

        restored_directories = sum(
            1
            for path in restored.rglob("*")
            if path.is_dir()
        )

        return FolderDecryptionResult(
            source_path=source,
            archive_path=archive_path,
            restored_folder=restored,
            decryption=decryption,
            restored_files=restored_files,
            restored_directories=restored_directories,
        )
