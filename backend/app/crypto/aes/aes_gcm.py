from app.crypto.interfaces.cipher import (
    SymmetricCipher,
)


class AESGCMCipher(
    SymmetricCipher
):

    def encrypt(
        self,
        plaintext: bytes,
        key: bytes,
    ) -> bytes:
        raise NotImplementedError

    def decrypt(
        self,
        ciphertext: bytes,
        key: bytes,
    ) -> bytes:
        raise NotImplementedError