from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime


MAGIC = b"SVLT"
VERSION = 1


@dataclass(slots=True)
class FileHeader:
    """
    Header written at the beginning of every encrypted file.
    """

    version: int = VERSION

    algorithm: str = "AES-256-GCM"

    key_algorithm: str = "RSA-4096-OAEP"

    hash_algorithm: str = "SHA-256"

    chunk_size: int = 4 * 1024 * 1024

    created_at: datetime = datetime.now(
        UTC
    )