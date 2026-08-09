from __future__ import annotations

import base64
import secrets

from cryptography.hazmat.primitives.asymmetric.rsa import (
    RSAPrivateKey,
    RSAPublicKey,
)

from app.crypto.aes.aes_gcm import AESGCMCipher
from app.crypto.exceptions import (
    DecryptionError,
    EncryptionError,
)
from app.crypto.models.encrypted_payload import (
    EncryptedPayload,
)
from app.crypto.models.hybrid_payload import (
    HybridEncryptedPayload,
)
from app.crypto.rsa.rsa_service import RSAService


class HybridEncryptor:
    """
    Provides hybrid encryption using AES-256-GCM for data encryption
    and RSA-4096 OAEP for wrapping the AES session key.
    """

    SESSION_KEY_SIZE = 32

    def __init__(
        self,
        aes_cipher: AESGCMCipher | None = None,
        rsa_service: RSAService | None = None,
    ) -> None:

        self._aes = aes_cipher or AESGCMCipher()

        self._rsa = rsa_service or RSAService()

    # ---------------------------------------------------------
    # Session Key Management
    # ---------------------------------------------------------

    def generate_session_key(self) -> bytes:
        """
        Generate a random AES-256 session key.
        """

        return secrets.token_bytes(
            self.SESSION_KEY_SIZE
        )

    # ---------------------------------------------------------
    # RSA Key Wrapping
    # ---------------------------------------------------------

    def wrap_key(
        self,
        session_key: bytes,
        public_key: RSAPublicKey,
    ) -> bytes:
        """
        Encrypt an AES session key using RSA OAEP.
        """

        return self._rsa.encrypt(
            session_key,
            public_key,
        )

    def unwrap_key(
        self,
        wrapped_key: bytes,
        private_key: RSAPrivateKey,
    ) -> bytes:
        """
        Recover the AES session key.
        """

        return self._rsa.decrypt(
            wrapped_key,
            private_key,
        )

    # ---------------------------------------------------------
    # Convenience Hybrid Encryption
    # ---------------------------------------------------------

    def encrypt(
        self,
        plaintext: bytes,
        public_key: RSAPublicKey,
        aad: bytes | None = None,
    ) -> HybridEncryptedPayload:

        try:

            session_key = (
                self.generate_session_key()
            )

            encrypted = self._aes.encrypt(
                plaintext=plaintext,
                key=session_key,
                aad=aad,
            )

            wrapped = self.wrap_key(
                session_key,
                public_key,
            )

            return HybridEncryptedPayload(
                encrypted_key=base64.b64encode(
                    wrapped
                ).decode(),

                nonce=encrypted.nonce,

                ciphertext=encrypted.ciphertext,

                tag=encrypted.tag,

                algorithm="AES-256-GCM",

                key_algorithm="RSA-4096-OAEP",

                hash_algorithm="SHA-256",

                version=1,
            )

        except Exception as exc:
            raise EncryptionError(
                str(exc)
            ) from exc

    # ---------------------------------------------------------
    # Convenience Hybrid Decryption
    # ---------------------------------------------------------

    def decrypt(
        self,
        payload: HybridEncryptedPayload,
        private_key: RSAPrivateKey,
        aad: bytes | None = None,
    ) -> bytes:

        try:

            wrapped = base64.b64decode(
                payload.encrypted_key
            )

            session_key = self.unwrap_key(
                wrapped,
                private_key,
            )

            encrypted_payload = EncryptedPayload(
                nonce=payload.nonce,
                ciphertext=payload.ciphertext,
                tag=payload.tag,
            )

            return self._aes.decrypt(
                payload=encrypted_payload,
                key=session_key,
                aad=aad,
            )

        except Exception as exc:
            raise DecryptionError(
                str(exc)
            ) from exc