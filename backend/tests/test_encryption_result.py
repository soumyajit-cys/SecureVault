from pathlib import Path

from app.crypto.file.file_header import FileHeader
from app.services.encryption.models import (
    EncryptionResult,
)


def test_encryption_result():

    result = EncryptionResult(
        source_path=Path("plain.txt"),
        encrypted_path=Path("plain.svlt"),
        file_size=100,
        encrypted_size=140,
        sha256="abc123",
        header=FileHeader(),
        wrapped_key_size=512,
        chunk_count=2,
    )

    assert result.success

    assert result.bytes_written == 140

    assert result.chunk_count == 2

    assert result.compression_ratio > 1