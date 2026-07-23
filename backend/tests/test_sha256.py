from app.crypto.hashing.sha256 import (
    SHA256Engine,
)


def test_hash_generation():

    engine = (
        SHA256Engine()
    )

    digest = engine.digest(
        b"securevault"
    )

    assert len(
        digest
    ) == 64