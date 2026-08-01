from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class FileMetadata:

    filename: str

    extension: str

    mime_type: str

    original_size: int

    encrypted_size: int = 0

    sha256: str = ""

    chunk_count: int = 0

    owner_id: str | None = None
