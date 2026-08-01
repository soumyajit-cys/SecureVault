from __future__ import annotations

from uuid import UUID

from app.crypto.exceptions import (
    DecryptionError,
    EncryptionError,
)

from app.crypto.models.hybrid_payload import (
    HybridEncryptedPayload,
)

from app.crypto.rsa.hybrid_encryptor import (
    HybridEncryptor,
)

from app.crypto.rsa.rsa_service import (
    RSAService,
)

from app.domain.models.crypto_key import (
    CryptoKey,
)

from app.services.key_management_service import (
    KeyManagementService,
)


class CryptoService:
    """
    Text-level hybrid encryption for a user's key pair.

    Encryption uses AES-256-GCM for the payload and wraps the AES
    session key with the user's RSA public key.  Decryption unwraps
    the session key with the private key held in key management.
    """

    def __init__(
        self,
        keys: KeyManagementService,
        hybrid: HybridEncryptor | None = None,
        rsa: RSAService | None = None,
    ) -> None:

        self._keys = keys

        self._hybrid = (
            hybrid or HybridEncryptor()
        )

        self._rsa = (
            rsa or RSAService()
        )

    # -------------------------------------------------
    # Encryption
    # -------------------------------------------------

    def encrypt_text(
        self,
        user_id: UUID,
        key: CryptoKey,
        plaintext: str,
    ) -> HybridEncryptedPayload:
        """
        Encrypt a text string with the user's key.

        Raises:
            EncryptionError: encryption failed.
        """

        if not plaintext:
            raise EncryptionError(
                "Cannot encrypt empty text."
            )

        public_key = self._rsa.load_public_key(
            key.public_key_pem.encode()
        )

        return self._hybrid.encrypt(
            plaintext.encode("utf-8"),
            public_key,
        )

    def encrypt_text_with_active_key(
        self,
        user_id: UUID,
        plaintext: str,
    ) -> HybridEncryptedPayload:
        """
        Convenience wrapper using the user's active key.
        """

        key = self._keys.get_active_key(
            user_id
        )

        return self.encrypt_text(
            user_id,
            key,
            plaintext,
        )

    # -------------------------------------------------
    # Decryption
    # -------------------------------------------------

    def decrypt_text(
        self,
        user_id: UUID,
        key: CryptoKey,
        payload: HybridEncryptedPayload,
    ) -> str:
        """
        Decrypt a hybrid payload back to plaintext.

        Raises:
            DecryptionError: unwrap or payload decryption failed.
        """

        private_key = self._keys.unlock_private_key(
            key
        )

        try:

            return self._hybrid.decrypt(
                payload,
                private_key,
            ).decode("utf-8")

        except DecryptionError:
            raise

        except Exception as exc:
            raise DecryptionError(
                f"Text decryption failed: {exc}"
            ) from exc

    def decrypt_text_with_active_key(
        self,
        user_id: UUID,
        payload: HybridEncryptedPayload,
    ) -> str:
        """
        Convenience wrapper using the user's active key.
        """

        key = self._keys.get_active_key(
            user_id
        )

        return self.decrypt_text(
            user_id,
            key,
            payload,
        )
