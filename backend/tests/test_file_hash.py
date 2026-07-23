from pathlib import Path

from app.crypto.hashing.sha256 import (
    SHA256Engine,
)


def test_file_hash(
    tmp_path: Path,
):

    sample = (
        tmp_path
        / "sample.txt"
    )

    sample.write_text(
        "SecureVault"
    )

    engine = (
        SHA256Engine()
    )

    digest = (
        engine.digest_file(
            sample
        )
    )

    assert len(
        digest
    ) == 64