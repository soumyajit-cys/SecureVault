from app.crypto.aes.aes_gcm import (
    AESGCMCipher,
)


def test_key_size():

    cipher = AESGCMCipher()

    key = (
        cipher.generate_key()
    )

    assert len(key) == 32