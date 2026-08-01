from __future__ import annotations

import base64
from datetime import UTC, datetime, timedelta
from uuid import UUID

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric.rsa import (
    RSAPrivateKey,
)
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

from app.core.config import get_settings
from app.crypto.aes.aes_gcm import AESGCMCipher
from app.crypto.exceptions import (
    DecryptionError,
    EncryptionError,
    InvalidKeyError,
)
from app.crypto.models.encrypted_payload import EncryptedPayload
from app.crypto.rsa.rsa_service import RSAService
from app.domain.models.crypto_key import CryptoKey
from app.domain.repositories.crypto_key_repository import (
    CryptoKeyRepository,
)

settings = get_settings()


class KeyNotFoundError(Exception):
    pass


class KeyRevokedError(Exception):
    pass


class KeyExpiredError(Exception):
    pass


class KeyManagementService:
    """
    Manages the lifecycle of user RSA encryption keys.

    Responsibilities:

    - generation of RSA-4096 key pairs
    - encrypted at-rest storage of private keys
    - key rotation with a replacement chain
    - automatic expiration
    - revocation
    - metadata (fingerprint, algorithm, key size, timestamps)
    """

    KEY_SIZE = 4096

    INFO_LABEL = b"securevault-private-key-encryption"

    def __init__(
        self,
        key_repository: CryptoKeyRepository,
        rsa_service: RSAService | None = None,
        aes_cipher: AESGCMCipher | None = None,
    ) -> None:

        self._keys = key_repository

        self._rsa = (
            rsa_service or RSAService()
        )

        self._aes = (
            aes_cipher or AESGCMCipher()
        )

    # -------------------------------------------------
    # Key Generation
    # -------------------------------------------------

    def generate_key_pair(
        self,
        user_id: UUID,
        name: str,
        validity_days: int = 365,
    ) -> CryptoKey:
        """
        Generate a new RSA-4096 key pair for a user and store the
        private key encrypted at rest.
        """

        keypair = self._rsa.generate_key_pair()

        public_pem = self._rsa.serialize_public_key(
            keypair.public_key
        )

        private_pem = self._rsa.serialize_private_key(
            keypair.private_key
        )

        encrypted, salt = (
            self._encrypt_private_key(
                private_pem
            )
        )

        expires_at = None

        if validity_days > 0:

            expires_at = (
                datetime.now(UTC)
                + timedelta(
                    days=validity_days
                )
            )

        entity = CryptoKey(
            user_id=user_id,
            name=name,
            algorithm="RSA-4096",
            key_size=self.KEY_SIZE,
            status="active",
            public_key_pem=public_pem.decode(),
            encrypted_private_key_pem=(
                encrypted.ciphertext
            ),
            private_key_nonce=encrypted.nonce,
            private_key_tag=encrypted.tag,
            private_key_salt=base64.b64encode(
                salt
            ).decode(),
            fingerprint=self._rsa.fingerprint(
                keypair.public_key
            ),
            expires_at=expires_at,
        )

        return self._keys.create(entity)

    # -------------------------------------------------
    # Key Lookup
    # -------------------------------------------------

    def get_key(
        self,
        user_id: UUID,
        key_id: UUID,
    ) -> CryptoKey:
        """
        Fetch one of the user's keys by id.

        Raises:
            KeyNotFoundError: key does not exist or belongs to
                another user.
        """

        key = self._keys.get_by_user_id(
            user_id,
            key_id,
        )

        if key is None:
            raise KeyNotFoundError(
                "Encryption key not found."
            )

        return key

    def list_keys(
        self,
        user_id: UUID,
        status: str | None = None,
    ) -> list[CryptoKey]:
        """
        List the user's keys, newest first.
        """

        return self._keys.list_by_user(
            user_id,
            status,
        )

    def get_active_key(
        self,
        user_id: UUID,
    ) -> CryptoKey:
        """
        Return the user's most recent active key.

        Raises:
            KeyNotFoundError: user has no active key.
        """

        key = self._keys.get_active_for_user(
            user_id
        )

        if key is None:
            raise KeyNotFoundError(
                "No active encryption key found. "
                "Generate one first."
            )

        return key

    # -------------------------------------------------
    # Private Key Unlock
    # -------------------------------------------------

    def unlock_private_key(
        self,
        key: CryptoKey,
    ) -> RSAPrivateKey:
        """
        Decrypt and load the stored private key.

        Raises:
            KeyRevokedError: key has been revoked.
            KeyExpiredError: key has expired.
            InvalidKeyError: at-rest decryption failed.
        """

        if key.is_revoked:
            raise KeyRevokedError(
                "Encryption key is revoked."
            )

        if key.is_expired:
            raise KeyExpiredError(
                "Encryption key is expired."
            )

        plaintext = self._decrypt_private_key(
            key
        )

        return self._rsa.load_private_key(
            plaintext
        )

    # -------------------------------------------------
    # Key Rotation
    # -------------------------------------------------

    def rotate_key(
        self,
        user_id: UUID,
        current_key_id: UUID,
        name: str | None = None,
        validity_days: int = 365,
    ) -> tuple[CryptoKey, CryptoKey]:
        """
        Rotate the user's key.

        The current key is revoked (keeping its history) and a new
        key is generated with a pointer back to the old one.

        Returns:
            (old_key, new_key)

        Raises:
            KeyNotFoundError: current key does not exist.
        """

        old_key = self.get_key(
            user_id,
            current_key_id,
        )

        new_key = self.generate_key_pair(
            user_id,
            name or f"{old_key.name}-rotated",
            validity_days,
        )

        old_key.status = "revoked"

        old_key.revoked_at = datetime.now(UTC)

        old_key.replaced_by_key_id = new_key.id

        self._keys.update(old_key)

        return old_key, new_key

    # -------------------------------------------------
    # Key Revocation
    # -------------------------------------------------

    def revoke_key(
        self,
        user_id: UUID,
        key_id: UUID,
    ) -> CryptoKey:
        """
        Immediately revoke a key so it can no longer be unlocked.

        Raises:
            KeyNotFoundError: key does not exist.
        """

        key = self.get_key(
            user_id,
            key_id,
        )

        if key.is_active:

            key.status = "revoked"

            key.revoked_at = datetime.now(UTC)

            self._keys.update(key)

        return key

    # -------------------------------------------------
    # Key Expiration
    # -------------------------------------------------

    def expire_old_keys(
        self,
    ) -> int:
        """
        Mark every active key past its expiry as expired.

        Returns:
            Number of keys transitioned to expired.
        """

        expired = self._keys.get_expired_keys(
            datetime.now(UTC)
        )

        return self._keys.mark_expired(
            expired
        )

    # -------------------------------------------------
    # Metadata
    # -------------------------------------------------

    def key_metadata(
        self,
        key: CryptoKey,
    ) -> dict:
        """
        Human readable metadata summary for a key.
        """

        return {
            "id": str(key.id),
            "name": key.name,
            "algorithm": key.algorithm,
            "key_size": key.key_size,
            "status": key.status,
            "fingerprint": key.fingerprint,
            "created_at": key.created_at.isoformat(),
            "expires_at": (
                key.expires_at.isoformat()
                if key.expires_at
                else None
            ),
            "revoked_at": (
                key.revoked_at.isoformat()
                if key.revoked_at
                else None
            ),
        }

    # -------------------------------------------------
    # At-Rest Encryption
    # -------------------------------------------------

    def _master_key(
        self,
        salt: bytes,
    ) -> bytes:
        """
        Derive a key-encryption key from the application secret.
        """

        hkdf = HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            info=self.INFO_LABEL,
        )

        return hkdf.derive(
            settings.SECRET_KEY.encode()
        )

    def _encrypt_private_key(
        self,
        private_pem: bytes,
    ) -> tuple[EncryptedPayload, bytes]:
        """
        Encrypt private key material with AES-256-GCM under a
        per-key derived master key.

        Returns:
            (encrypted payload, salt)
        """

        salt = self._aes.generate_nonce()

        master = self._master_key(
            salt
        )

        try:

            payload = self._aes.encrypt(
                plaintext=private_pem,
                key=master,
            )

            return payload, salt

        except Exception as exc:
            raise EncryptionError(
                f"Private key encryption failed: {exc}"
            ) from exc

    def _decrypt_private_key(
        self,
        key: CryptoKey,
    ) -> bytes:
        """
        Decrypt private key material.
        """

        try:

            salt = base64.b64decode(
                key.private_key_salt
            )

            master = self._master_key(
                salt
            )

            payload = EncryptedPayload(
                nonce=key.private_key_nonce,
                ciphertext=key.encrypted_private_key_pem,
                tag=key.private_key_tag,
            )

            return self._aes.decrypt(
                payload=payload,
                key=master,
            )

        except Exception as exc:
            raise InvalidKeyError(
                f"Private key decryption failed: {exc}"
            ) from exc
