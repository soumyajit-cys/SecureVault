from app.crypto.aes.aes_gcm import (
    AESGCMCipher,
)


class CryptoService:

    def __init__(
        self,
    ):
        self.cipher = (
            AESGCMCipher()
        )

    def encrypt_text(
        self,
        text: str,
        key: bytes,
    ):

        return self.cipher.encrypt(
            text.encode(),
            key,
        )

    def decrypt_text(
        self,
        payload,
        key: bytes,
    ):

        return (
            self.cipher.decrypt(
                payload,
                key,
            )
            .decode()
        )