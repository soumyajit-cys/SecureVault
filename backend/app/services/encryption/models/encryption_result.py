from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.crypto.file.file_header import FileHeader


@dataclass(slots=True)
class EncryptionResult:
    """
    Returned after a successful file encryption operation.
    """

    source_path: Path

    encrypted_path: Path

    file_size: int

    encrypted_size: int

    sha256: str

    header: FileHeader

    wrapped_key_size: int

    chunk_count: int

    success: bool = True

    message: str = "File encrypted successfully."

    @property
    def bytes_written(self) -> int:
        return self.encrypted_size

    @property
    def compression_ratio(self) -> float:
        """
        Ratio between encrypted and original size.

        Encryption normally increases size slightly because of:
        - GCM authentication tags
        - container header
        - RSA wrapped key
        """

        if self.file_size == 0:
            return 1.0

        return self.encrypted_size / self.file_size