from app.crypto.rsa.hybrid_encryptor import (
    HybridEncryptor,
)


def test_generate_session_key():

    hybrid = HybridEncryptor()

    key = hybrid.generate_session_key()

    assert len(key) == 32