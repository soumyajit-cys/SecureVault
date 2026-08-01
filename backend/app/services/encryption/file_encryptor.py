from __future__ import annotations

import hashlib
import mimetypes
from datetime import UTC, datetime
from pathlib import Path
from typing import BinaryIO

from cryptography.hazmat.primitives.asymmetric.rsa import (
    RSAPublicKey,
)

from app.crypto.exceptions import (
    EncryptionError,
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

from app.crypto.streams.chunk_reader import (
    ChunkReader,
)

from app.crypto.streams.constants import (
    DEFAULT_CHUNK_SIZE,
)

from app.crypto.streams.encrypt_stream import (
    EncryptStream,
)

from app.services.encryption.container_serializer import (
    ContainerSerializer,
)

from app.services.encryption.models.encryption_result import (
    EncryptionResult,
)


class FileEncryptor:
    """
    Encrypts files of any size into the SecureVault container format.

    The source file is read lazily in fixed-size chunks, so memory
    usage stays constant regardless of the file size.  Binary and
    textual content are handled identically.

    Integrity is guaranteed by:

    - AES-256-GCM authentication tags on every chunk
    - a SHA-256 digest of the original file stored in the container
      metadata and re-verified after decryption
    """

    def __init__(
        self,
        serializer: ContainerSerializer | None = None,
        chunk_reader: ChunkReader | None = None,
        encrypt_stream: EncryptStream | None = None,
        hybrid: HybridEncryptor | None = None,
    ) -> None:

        self._serializer = (
            serializer or ContainerSerializer()
        )

        self._chunk_reader = (
            chunk_reader or ChunkReader()
        )

        self._encrypt_stream = (
            encrypt_stream or EncryptStream()
        )

        self._hybrid = (
            hybrid or HybridEncryptor()
        )

    # -------------------------------------------------
    # Public API
    # -------------------------------------------------

    def encrypt_file(
        self,
        source_path: str | Path,
        public_key: RSAPublicKey,
        output_path: str | Path | None = None,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        owner_id: str | None = None,
    ) -> EncryptionResult:
        """
        Encrypt a single file into a SecureVault container.

        Args:
            source_path: file to encrypt (binary or text).
            public_key: RSA public key used to wrap the session key.
            output_path: optional destination container path.
                Defaults to ``<source>.svlt`` beside the source file.
            chunk_size: plaintext chunk size in bytes.
            owner_id: optional owner identifier stored in metadata.

        Raises:
            EncryptionError: when the source file cannot be read or
                the encryption pipeline fails.
        """

        source = Path(source_path)

        if not source.is_file():
            raise EncryptionError(
                f"Source file not found: {source}"
            )

        output = (
            Path(output_path)
            if output_path
            else source.with_suffix(
                source.suffix + ".svlt"
            )
        )

        session_key = (
            self._hybrid.generate_session_key()
        )

        wrapped_key = self._hybrid.wrap_key(
            session_key,
            public_key,
        )

        header = FileHeader(
            chunk_size=chunk_size,
            created_at=datetime.now(UTC),
        )

        metadata = self._build_metadata(
            source,
            wrapped_key,
            owner_id,
        )

        stream = self._serializer.write_file(
            output,
            header,
            wrapped_key,
            metadata,
        )

        try:

            sha256 = self._encrypt_chunks(
                source,
                stream,
                session_key,
                header.chunk_size,
                metadata,
            )

        except Exception as exc:

            stream.close()

            output.unlink(
                missing_ok=True
            )

            raise EncryptionError(
                f"File encryption failed: {exc}"
            ) from exc

        finally:

            if not stream.closed:
                stream.close()

        metadata.sha256 = sha256

        return EncryptionResult(
            source_path=source,
            encrypted_path=output,
            file_size=metadata.original_size,
            encrypted_size=metadata.encrypted_size,
            sha256=sha256,
            header=header,
            wrapped_key_size=len(wrapped_key),
            chunk_count=metadata.chunk_count,
        )

    def encrypt_to_stream(
        self,
        source_path: str | Path,
        public_key: RSAPublicKey,
        stream: BinaryIO,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        owner_id: str | None = None,
    ) -> EncryptionResult:
        """
        Encrypt a file directly into an open binary stream.

        Useful when the encrypted bytes are streamed to a client or
        into object storage without touching disk.
        """

        source = Path(source_path)

        if not source.is_file():
            raise EncryptionError(
                f"Source file not found: {source}"
            )

        session_key = (
            self._hybrid.generate_session_key()
        )

        wrapped_key = self._hybrid.wrap_key(
            session_key,
            public_key,
        )

        header = FileHeader(
            chunk_size=chunk_size,
            created_at=datetime.now(UTC),
        )

        metadata = self._build_metadata(
            source,
            wrapped_key,
            owner_id,
        )

        self._serializer.write_header(
            stream,
            header,
            metadata,
        )

        self._serializer.write_wrapped_key(
            stream,
            wrapped_key,
        )

        sha256 = self._encrypt_chunks(
            source,
            stream,
            session_key,
            header.chunk_size,
            metadata,
        )

        metadata.sha256 = sha256

        return EncryptionResult(
            source_path=source,
            encrypted_path=source.with_suffix(
                source.suffix + ".svlt"
            ),
            file_size=metadata.original_size,
            encrypted_size=metadata.encrypted_size,
            sha256=sha256,
            header=header,
            wrapped_key_size=len(wrapped_key),
            chunk_count=metadata.chunk_count,
        )

    # -------------------------------------------------
    # Internals
    # -------------------------------------------------

    def _encrypt_chunks(
        self,
        source: Path,
        stream: BinaryIO,
        session_key: bytes,
        chunk_size: int,
        metadata: FileMetadata,
    ) -> str:
        """
        Single-pass stream encryption that also computes the
        SHA-256 digest of the original file.
        """

        sha256 = hashlib.sha256()

        chunk_count = 0

        encrypted_size = 0

        for chunk in (
            self._chunk_reader.read(source)
        ):

            sha256.update(chunk)

            for payload in (
                self._encrypt_stream.encrypt(
                    [chunk],
                    session_key,
                )
            ):

                self._serializer.write_chunk(
                    stream,
                    payload,
                )

                chunk_count += 1

                encrypted_size += (
                    len(payload.nonce)
                    + len(payload.tag)
                    + len(payload.ciphertext)
                )

        metadata.chunk_count = chunk_count

        metadata.encrypted_size = encrypted_size

        metadata.sha256 = sha256.hexdigest()

        return metadata.sha256

    @staticmethod
    def _build_metadata(
        source: Path,
        wrapped_key: bytes,
        owner_id: str | None,
    ) -> FileMetadata:
        """
        Generate metadata describing the original file.
        """

        extension = (
            source.suffix.lstrip(".").lower()
        )

        mime_type = (
            mimetypes.guess_type(source.name)[0]
            or "application/octet-stream"
        )

        original_size = (
            source.stat().st_size
        )

        return FileMetadata(
            filename=source.name,
            extension=extension,
            mime_type=mime_type,
            original_size=original_size,
            encrypted_size=len(wrapped_key),
            sha256="",
            owner_id=owner_id,
        )
