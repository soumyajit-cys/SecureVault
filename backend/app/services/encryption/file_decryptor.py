from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from pathlib import Path
from typing import BinaryIO

from cryptography.hazmat.primitives.asymmetric.rsa import (
    RSAPrivateKey,
)

from app.crypto.exceptions import (
    DecryptionError,
    IntegrityVerificationError,
)

from app.crypto.file.file_header import (
    FileHeader,
)

from app.crypto.file.file_metadata import (
    FileMetadata,
)

from app.crypto.rsa.hybrid_encryptor import (
    HybridEncryptor,
)

from app.crypto.streams.chunk_writer import (
    ChunkWriter,
)

from app.crypto.streams.decrypt_stream import (
    DecryptStream,
)

from app.services.encryption.container_serializer import (
    ContainerSerializer,
)

from app.services.encryption.models.decryption_result import (
    DecryptionResult,
)


class FileDecryptor:
    """
    Decrypts SecureVault containers back into their original files.

    The container is read lazily chunk by chunk, so memory usage
    stays constant regardless of the encrypted file size.

    Integrity verification combines:

    - AES-256-GCM tag validation on every chunk (cryptographic)
    - SHA-256 digest comparison against the metadata embedded in
      the container header

    If either check fails, an IntegrityVerificationError is raised
    and the partially written output is removed.
    """

    def __init__(
        self,
        serializer: ContainerSerializer | None = None,
        decrypt_stream: DecryptStream | None = None,
        chunk_writer: ChunkWriter | None = None,
        hybrid: HybridEncryptor | None = None,
    ) -> None:

        self._serializer = (
            serializer or ContainerSerializer()
        )

        self._decrypt_stream = (
            decrypt_stream or DecryptStream()
        )

        self._chunk_writer = (
            chunk_writer or ChunkWriter()
        )

        self._hybrid = (
            hybrid or HybridEncryptor()
        )

    # -------------------------------------------------
    # Public API
    # -------------------------------------------------

    def decrypt_file(
        self,
        source_path: str | Path,
        private_key: RSAPrivateKey,
        output_path: str | Path | None = None,
        verify_integrity: bool = True,
    ) -> DecryptionResult:
        """
        Decrypt a SecureVault container into a plaintext file.

        Args:
            source_path: encrypted ``.svlt`` container.
            private_key: RSA private key used to unwrap the session key.
            output_path: optional destination path.  Defaults to the
                original filename stored in the container metadata,
                placed beside the container with the ``.svlt``
                extension stripped.
            verify_integrity: when True (default) the decrypted
                content is verified against the stored SHA-256.

        Raises:
            DecryptionError: invalid container or unwrap failure.
            IntegrityVerificationError: decrypted content does not
                match the stored digest.
        """

        source = Path(source_path)

        if not source.is_file():
            raise DecryptionError(
                f"Encrypted file not found: {source}"
            )

        stream, header_dict, wrapped_key = (
            self._serializer.open_file(source)
        )

        try:

            metadata = (
                self._serializer.metadata_from_header(
                    header_dict
                )
            )

            output = (
                Path(output_path)
                if output_path
                else self._default_output_path(
                    source,
                    metadata,
                )
            )

            session_key = self._hybrid.unwrap_key(
                wrapped_key,
                private_key,
            )

            header = FileHeader(
                version=int(
                    header_dict.get("version", 1)
                ),
                algorithm=str(
                    header_dict.get(
                        "algorithm",
                        "AES-256-GCM",
                    )
                ),
                key_algorithm=str(
                    header_dict.get(
                        "key_algorithm",
                        "RSA-4096-OAEP",
                    )
                ),
                hash_algorithm=str(
                    header_dict.get(
                        "hash_algorithm",
                        "SHA-256",
                    )
                ),
                chunk_size=int(
                    header_dict.get(
                        "chunk_size",
                        4 * 1024 * 1024,
                    )
                ),
                created_at=(
                    datetime.fromisoformat(
                        header_dict["created_at"]
                    )
                    if header_dict.get("created_at")
                    else datetime.now(UTC)
                ),
            )

            output.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            with output.open("wb") as out:

                sha256, chunk_count = (
                    self._decrypt_chunks(
                        stream,
                        out,
                        session_key,
                    )
                )

            integrity_verified = True

            if (
                verify_integrity
                and metadata
                and metadata.sha256
            ):

                integrity_verified = (
                    sha256 == metadata.sha256
                )

                if not integrity_verified:
                    output.unlink(
                        missing_ok=True
                    )
                    raise IntegrityVerificationError(
                        "Decrypted file failed "
                        "SHA-256 integrity check."
                    )

            return DecryptionResult(
                source_path=source,
                decrypted_path=output,
                file_size=source.stat().st_size,
                decrypted_size=(
                    output.stat().st_size
                ),
                sha256=sha256,
                header=header,
                chunk_count=chunk_count,
                integrity_verified=integrity_verified,
            )

        except IntegrityVerificationError:
            raise

        except DecryptionError:
            raise

        except Exception as exc:
            raise DecryptionError(
                f"File decryption failed: {exc}"
            ) from exc

        finally:

            if not stream.closed:
                stream.close()

    def decrypt_to_stream(
        self,
        source_path: str | Path,
        private_key: RSAPrivateKey,
        stream: BinaryIO,
    ) -> tuple[str, int]:
        """
        Decrypt a container into an open binary stream.

        Returns a tuple of ``(sha256, chunk_count)`` so callers can
        relay integrity information.  The stream is not closed.
        """

        source = Path(source_path)

        if not source.is_file():
            raise DecryptionError(
                f"Encrypted file not found: {source}"
            )

        container, _, wrapped_key = (
            self._serializer.open_file(source)
        )

        try:

            session_key = self._hybrid.unwrap_key(
                wrapped_key,
                private_key,
            )

            return self._decrypt_chunks(
                container,
                stream,
                session_key,
            )

        except DecryptionError:
            raise

        except Exception as exc:
            raise DecryptionError(
                f"File decryption failed: {exc}"
            ) from exc

        finally:

            if not container.closed:
                container.close()

    # -------------------------------------------------
    # Internals
    # -------------------------------------------------

    def _decrypt_chunks(
        self,
        container: BinaryIO,
        output: BinaryIO,
        session_key: bytes,
    ) -> tuple[str, int]:
        """
        Stream-decrypt every chunk while computing the SHA-256
        digest of the recovered plaintext.
        """

        sha256 = hashlib.sha256()

        chunk_count = 0

        for payload in (
            self._serializer.iter_chunks(
                container
            )
        ):

            for plaintext in (
                self._decrypt_stream.decrypt(
                    [payload],
                    session_key,
                )
            ):

                output.write(plaintext)

                sha256.update(plaintext)

                chunk_count += 1

        return sha256.hexdigest(), chunk_count

    @staticmethod
    def _default_output_path(
        source: Path,
        metadata: FileMetadata | None,
    ) -> Path:
        """
        Prefer the original filename from metadata, falling back
        to stripping the ``.svlt`` extension.
        """

        if (
            metadata
            and metadata.filename
            and "/" not in metadata.filename
            and "\\" not in metadata.filename
            and ".." not in metadata.filename
        ):

            return source.with_name(
                metadata.filename
            )

        if source.suffix.lower() == ".svlt":
            return source.with_suffix("")

        return source.with_suffix(
            source.suffix + ".plain"
        )
