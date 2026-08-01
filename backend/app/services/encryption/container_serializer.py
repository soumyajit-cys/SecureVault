from __future__ import annotations

import json
import struct
from pathlib import Path
from typing import BinaryIO

from app.crypto.file.file_header import FileHeader
from app.crypto.models.encrypted_payload import EncryptedPayload

MAGIC = b"SVLT"
FORMAT_VERSION = 1


class InvalidContainerError(Exception):
    """Raised when an encrypted SecureVault container is invalid."""


class ContainerSerializer:
    """
    Handles reading and writing SecureVault encrypted containers.

    Container Layout

    +------------------------------------------------+
    | MAGIC (4 bytes)                                |
    +------------------------------------------------+
    | VERSION (4 bytes)                              |
    +------------------------------------------------+
    | HEADER_LENGTH (4 bytes)                        |
    +------------------------------------------------+
    | HEADER (JSON)                                  |
    +------------------------------------------------+
    | WRAPPED_KEY_LENGTH (4 bytes)                   |
    +------------------------------------------------+
    | WRAPPED_KEY                                    |
    +------------------------------------------------+
    | CHUNK                                           |
    | CHUNK                                           |
    | CHUNK                                           |
    | ...                                             |
    +------------------------------------------------+

    Chunk Layout

    +---------------------------------------------+
    | NONCE_LENGTH (4 bytes)                      |
    +---------------------------------------------+
    | NONCE                                       |
    +---------------------------------------------+
    | TAG_LENGTH (4 bytes)                        |
    +---------------------------------------------+
    | TAG                                         |
    +---------------------------------------------+
    | CIPHERTEXT_LENGTH (4 bytes)                 |
    +---------------------------------------------+
    | CIPHERTEXT                                  |
    +---------------------------------------------+
    """

    # -------------------------------------------------
    # Header
    # -------------------------------------------------

    def write_header(
        self,
        stream: BinaryIO,
        header: FileHeader,
    ) -> None:

        header_dict = {
            "version": header.version,
            "algorithm": header.algorithm,
            "key_algorithm": header.key_algorithm,
            "hash_algorithm": header.hash_algorithm,
            "chunk_size": header.chunk_size,
            "created_at": header.created_at.isoformat(),
        }

        header_bytes = json.dumps(
            header_dict,
            separators=(",", ":"),
        ).encode("utf-8")

        stream.write(MAGIC)

        stream.write(
            struct.pack(">I", FORMAT_VERSION)
        )

        stream.write(
            struct.pack(">I", len(header_bytes))
        )

        stream.write(header_bytes)

    def read_header(
        self,
        stream: BinaryIO,
    ) -> dict:

        magic = self._read_exact(stream, 4)

        if magic != MAGIC:
            raise InvalidContainerError(
                "Invalid SecureVault container."
            )

        version = struct.unpack(
            ">I",
            self._read_exact(stream, 4),
        )[0]

        if version != FORMAT_VERSION:
            raise InvalidContainerError(
                f"Unsupported container version: {version}"
            )

        header_length = struct.unpack(
            ">I",
            self._read_exact(stream, 4),
        )[0]

        header_bytes = self._read_exact(
            stream,
            header_length,
        )

        return json.loads(
            header_bytes.decode("utf-8")
        )

    # -------------------------------------------------
    # Wrapped AES Session Key
    # -------------------------------------------------

    def write_wrapped_key(
        self,
        stream: BinaryIO,
        wrapped_key: bytes,
    ) -> None:

        stream.write(
            struct.pack(">I", len(wrapped_key))
        )

        stream.write(wrapped_key)

    def read_wrapped_key(
        self,
        stream: BinaryIO,
    ) -> bytes:

        key_length = struct.unpack(
            ">I",
            self._read_exact(stream, 4),
        )[0]

        return self._read_exact(
            stream,
            key_length,
        )

    # -------------------------------------------------
    # Chunk Serialization
    # -------------------------------------------------

    def write_chunk(
        self,
        stream: BinaryIO,
        payload: EncryptedPayload,
    ) -> None:

        nonce = payload.nonce.encode("utf-8")
        tag = payload.tag.encode("utf-8")
        ciphertext = payload.ciphertext.encode("utf-8")

        stream.write(
            struct.pack(">I", len(nonce))
        )

        stream.write(nonce)

        stream.write(
            struct.pack(">I", len(tag))
        )

        stream.write(tag)

        stream.write(
            struct.pack(">I", len(ciphertext))
        )

        stream.write(ciphertext)

    def read_chunk(
        self,
        stream: BinaryIO,
    ) -> EncryptedPayload | None:

        length_bytes = stream.read(4)

        if length_bytes == b"":
            return None

        if len(length_bytes) != 4:
            raise InvalidContainerError(
                "Corrupted encrypted container."
            )

        nonce_length = struct.unpack(
            ">I",
            length_bytes,
        )[0]

        nonce = self._read_exact(
            stream,
            nonce_length,
        ).decode("utf-8")

        tag_length = struct.unpack(
            ">I",
            self._read_exact(stream, 4),
        )[0]

        tag = self._read_exact(
            stream,
            tag_length,
        ).decode("utf-8")

        cipher_length = struct.unpack(
            ">I",
            self._read_exact(stream, 4),
        )[0]

        ciphertext = self._read_exact(
            stream,
            cipher_length,
        ).decode("utf-8")

        return EncryptedPayload(
            nonce=nonce,
            tag=tag,
            ciphertext=ciphertext,
        )

    def iter_chunks(
        self,
        stream: BinaryIO,
    ):

        while True:

            chunk = self.read_chunk(stream)

            if chunk is None:
                break

            yield chunk

    # -------------------------------------------------
    # File Helpers
    # -------------------------------------------------

    def write_file(
        self,
        path: Path,
        header: FileHeader,
        wrapped_key: bytes,
    ) -> BinaryIO:

        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        stream = path.open("wb")

        self.write_header(
            stream,
            header,
        )

        self.write_wrapped_key(
            stream,
            wrapped_key,
        )

        return stream

    def open_file(
        self,
        path: Path,
    ) -> tuple[BinaryIO, dict, bytes]:

        stream = path.open("rb")

        header = self.read_header(
            stream,
        )

        wrapped_key = self.read_wrapped_key(
            stream,
        )

        return (
            stream,
            header,
            wrapped_key,
        )

    # -------------------------------------------------
    # Internal Helpers
    # -------------------------------------------------

    @staticmethod
    def _read_exact(
        stream: BinaryIO,
        size: int,
    ) -> bytes:

        data = stream.read(size)

        if len(data) != size:
            raise InvalidContainerError(
                "Unexpected end of encrypted container."
            )

        return data