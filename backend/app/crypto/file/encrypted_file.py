from __future__ import annotations

from dataclasses import dataclass

from app.crypto.file.file_header import (
    FileHeader,
)

from app.crypto.file.file_metadata import (
    FileMetadata,
)


@dataclass(slots=True)
class EncryptedFile:

    header: FileHeader

    metadata: FileMetadata

    encrypted_key: bytes

    path: str