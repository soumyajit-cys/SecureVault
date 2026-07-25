from __future__ import annotations

import base64

from cryptography.hazmat.primitives.asymmetric.rsa import (
    RSAPrivateKey,
    RSAPublicKey,
)

from app.crypto.aes.aes_gcm import AESGCMCipher
from app.crypto.exceptions import (
    DecryptionError,
    EncryptionError,
)
from app.crypto.models.hybrid_payload import (
    HybridEncryptedPayload,
)
from app.crypto.rsa.rsa_service import RSAService


class HybridEncryptor:

    def __init__(self):

        self._aes = AESGCMCipher()

        self._rsa = RSAService()

    def encrypt(
        self,
        plaintext: bytes,
        public_key: RSAPublicKey,
    ) -> HybridEncryptedPayload:

        try:

            aes_key = self._aes.generate_key()

            encrypted_payload = self._aes.encrypt(
                plaintext,
                aes_key,
            )

            wrapped_key = self._rsa.encrypt(
                aes_key,
                public_key,
            )

            return HybridEncryptedPayload(
                encrypted_key=base64.b64encode(
                    wrapped_key
                ).decode(),

                nonce=encrypted_payload.nonce,

                ciphertext=encrypted_payload.ciphertext,

                tag=encrypted_payload.tag,

                algorithm="AES-256-GCM",

                key_algorithm="RSA-4096-OAEP",

                hash_algorithm="SHA-256",

                version=1,
            )

        except Exception as exc:

            raise EncryptionError(
                str(exc)
            ) from exc

    def decrypt(
        self,
        payload: HybridEncryptedPayload,
        private_key: RSAPrivateKey,
    ) -> bytes:

        try:

            wrapped_key = base64.b64decode(
                payload.encrypted_key
            )

            aes_key = self._rsa.decrypt(
                wrapped_key,
                private_key,
            )

            from app.crypto.models.encrypted_payload import (
                EncryptedPayload,
            )

            encrypted = EncryptedPayload(
                nonce=payload.nonce,

                ciphertext=payload.ciphertext,

                tag=payload.tag,
            )

            return self._aes.decrypt(
                encrypted,
                aes_key,
            )

        except Exception as exc:

            raise DecryptionError(
                str(exc)
            ) from exc