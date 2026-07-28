from app.crypto.aes.aes_gcm import AESGCMCipher
from app.crypto.streams.decrypt_stream import DecryptStream
from app.crypto.streams.encrypt_stream import EncryptStream


def test_encrypt_decrypt_stream():

    cipher = AESGCMCipher()

    key = cipher.generate_key()

    plaintext = [
        b"one",
        b"two",
        b"three",
        b"four",
    ]

    encrypted = list(
        EncryptStream(cipher).encrypt(
            plaintext,
            key,
        )
    )

    decrypted = list(
        DecryptStream(cipher).decrypt(
            encrypted,
            key,
        )
    )

    assert plaintext == decrypted