import pytest

from app.crypto.aes.aes_gcm import (
    AESGCMCipher,
)

from app.crypto.exceptions import (
    DecryptionError,
)


def test_tampered_ciphertext():

    cipher = AESGCMCipher()

    key = (
        cipher.generate_key()
    )

    payload = (
        cipher.encrypt(
            b"Secret",
            key,
        )
    )

    payload.ciphertext = (
        payload.ciphertext[:-2]
        + "AA"
    )

    with pytest.raises(
        DecryptionError
    ):
        cipher.decrypt(
            payload,
            key,
        )