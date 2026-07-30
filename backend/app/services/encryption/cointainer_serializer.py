from __future__ import annotations

import json
import struct
from pathlib import Path
from typing import BinaryIO

from app.crypto.file.file_header import FileHeader

from app.crypto.models.encrypted_payload import (
    EncryptedPayload,
)

MAGIC = b"SVLT"
FORMAT_VERSION = 1


class InvalidContainerError(Exception):
    """Raised when a SecureVault container is invalid."""


class ContainerSerializer:
    """
    Reads and writes SecureVault encrypted container headers.

    Container Layout:

    +-------------------------------+
    | MAGIC (4 bytes)               |
    +-------------------------------+
    | VERSION (4 bytes)             |
    +-------------------------------+
    | HEADER_LENGTH (4 bytes)       |
    +-------------------------------+
    | JSON HEADER                   |
    +-------------------------------+
    | WRAPPED_KEY_LENGTH (4 bytes)  |
    +-------------------------------+
    | WRAPPED_KEY                   |
    +-------------------------------+
    | ENCRYPTED DATA ...            |
    +-------------------------------+
    """

    def write_header(
        self,
        stream: BinaryIO,
        header: FileHeader,
    ) -> None:
        """
        Write the SecureVault header.
        """

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
        """
        Read a SecureVault header.
        """

        magic = stream.read(4)

        if magic != MAGIC:
            raise InvalidContainerError(
                "Invalid SecureVault container."
            )

        version = struct.unpack(
            ">I",
            stream.read(4),
        )[0]

        if version != FORMAT_VERSION:
            raise InvalidContainerError(
                f"Unsupported container version: {version}"
            )

        header_length = struct.unpack(
            ">I",
            stream.read(4),
        )[0]

        header_data = stream.read(
            header_length
        )

        return json.loads(
            header_data.decode("utf-8")
        )

    def write_wrapped_key(
        self,
        stream: BinaryIO,
        wrapped_key: bytes,
    ) -> None:
        """
        Store the RSA-encrypted AES session key.
        """

        stream.write(
            struct.pack(">I", len(wrapped_key))
        )

        stream.write(wrapped_key)

    def read_wrapped_key(
        self,
        stream: BinaryIO,
    ) -> bytes:
        """
        Read the RSA-wrapped AES session key.
        """

        key_length = struct.unpack(
            ">I",
            stream.read(4),
        )[0]

        return stream.read(
            key_length
        )

    def write_file(
        self,
        path: Path,
        header: FileHeader,
        wrapped_key: bytes,
    ) -> BinaryIO:
        """
        Create a new SecureVault container and write its header.

        Returns an open binary stream positioned immediately after
        the wrapped session key so encrypted payloads can be written.
        """

        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        stream = path.open(
            "wb"
        )

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
        """
        Open an existing SecureVault container.

        Returns:
            (
                binary_stream,
                header_dict,
                wrapped_key,
            )
        """

        stream = path.open(
            "rb"
        )

        header = self.read_header(
            stream
        )

        wrapped_key = self.read_wrapped_key(
            stream
        )

        return (
            stream,
            header,
            wrapped_key,
        )