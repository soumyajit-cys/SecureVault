from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.crypto.file.file_header import FileHeader


@dataclass(slots=True)
class DecryptionResult:
    """
    Returned after a successful file decryption operation.
    """

    source_path: Path

    decrypted_path: Path

    file_size: int

    decrypted_size: int

    sha256: str

    header: FileHeader

    chunk_count: int

    integrity_verified: bool = True

    success: bool = True

    message: str = "File decrypted successfully."

    @property
    def bytes_written(self) -> int:
        return self.decrypted_size

    @property
    def expansion_ratio(self) -> float:
        """
        Ratio between decrypted and encrypted source size.

        Values below 1.0 indicate container overhead.
        """

        if self.file_size == 0:
            return 1.0

        return self.decrypted_size / self.file_size
