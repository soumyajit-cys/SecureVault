import base64
import os

from cryptography.hazmat.primitives.ciphers.aead import (
    AESGCM,
)

from app.crypto.exceptions import (
    DecryptionError,
    EncryptionError,
)

from app.crypto.interfaces.cipher import (
    SymmetricCipher,
)

from app.crypto.models.encrypted_payload import (
    EncryptedPayload,
)


class AESGCMCipher(
    SymmetricCipher
):

    NONCE_SIZE = 12

    KEY_SIZE = 32

    def generate_key(
        self,
    ) -> bytes:

        return os.urandom(
            self.KEY_SIZE
        )

    def generate_nonce(
        self,
    ) -> bytes:

        return os.urandom(
            self.NONCE_SIZE
        )

    def encrypt(
        self,
        plaintext: bytes,
        key: bytes,
    ) -> EncryptedPayload:

        try:

            aes = AESGCM(key)

            nonce = (
                self.generate_nonce()
            )

            encrypted = aes.encrypt(
                nonce,
                plaintext,
                None,
            )

            ciphertext = (
                encrypted[:-16]
            )

            tag = (
                encrypted[-16:]
            )

            return EncryptedPayload(
                nonce=base64.b64encode(
                    nonce
                ).decode(),
                ciphertext=base64.b64encode(
                    ciphertext
                ).decode(),
                tag=base64.b64encode(
                    tag
                ).decode(),
            )

        except Exception as exc:
            raise EncryptionError(
                str(exc)
            )

    def decrypt(
        self,
        payload: EncryptedPayload,
        key: bytes,
    ) -> bytes:

        try:

            aes = AESGCM(key)

            nonce = (
                base64.b64decode(
                    payload.nonce
                )
            )

            ciphertext = (
                base64.b64decode(
                    payload.ciphertext
                )
            )

            tag = (
                base64.b64decode(
                    payload.tag
                )
            )

            encrypted = (
                ciphertext
                + tag
            )

            return aes.decrypt(
                nonce,
                encrypted,
                None,
            )

        except Exception as exc:
            raise DecryptionError(
                str(exc)
            )