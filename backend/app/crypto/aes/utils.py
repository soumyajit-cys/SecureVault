from app.crypto.aes.aes_gcm import (
    AESGCMCipher,
)

cipher = AESGCMCipher()


def generate_aes_key():
    return cipher.generate_key()