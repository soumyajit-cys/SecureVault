from app.crypto.hashing.sha256 import (
    SHA256Engine,
)


def test_hash_verification():

    engine = (
        SHA256Engine()
    )

    data = b"hello"

    digest = engine.digest(
        data
    )

    assert (
        engine.verify(
            data,
            digest,
        )
        is True
    )