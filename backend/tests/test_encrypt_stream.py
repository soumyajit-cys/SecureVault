from app.crypto.aes.aes_gcm import AESGCMCipher
from app.crypto.streams.encrypt_stream import EncryptStream


def test_encrypt_stream():

    cipher = AESGCMCipher()

    key = cipher.generate_key()

    chunks = [
        b"hello",
        b"world",
        b"securevault",
    ]

    encrypted = list(
        EncryptStream(cipher).encrypt(
            chunks,
            key,
        )
    )

    assert len(encrypted) == 3

    assert encrypted[0].ciphertext