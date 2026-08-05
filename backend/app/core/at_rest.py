"""
Shared at-rest encryption for sensitive material (private keys).

Every secret is wrapped with AES-256-GCM under a per-object
key derived from the application SECRET_KEY via HKDF-SHA256 with
a random salt and a domain-separation info label. Ciphertext,
nonce, tag and salt are base64-encoded for storage as strings.
"""

from __future__ import annotations

import base64
from dataclasses import dataclass

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

from app.core.config import get_settings
from app.crypto.aes.aes_gcm import AESGCMCipher
from app.crypto.exceptions import (
    DecryptionError,
    EncryptionError,
    InvalidKeyError,
)
from app.crypto.models.encrypted_payload import EncryptedPayload

INFO_LABEL = b"securevault-at-rest-encryption-v1"


@dataclass(frozen=True)
class EncryptedSecret:
    """Base64-encoded envelope produced by :func:`encrypt_secret`."""

    ciphertext: str
    nonce: str
    tag: str
    salt: str

    def is_set(self) -> bool:
        return bool(self.ciphertext and self.nonce and self.tag and self.salt)


def encrypt_secret(
    plaintext: bytes,
    info_label: bytes = INFO_LABEL,
) -> EncryptedSecret:
    """
    Wrap ``plaintext`` with AES-256-GCM under a derived key.

    Raises:
        EncryptionError: wrapping failed.
    """

    settings = get_settings()

    aes = AESGCMCipher()

    salt = aes.generate_nonce()

    master = _derive_master_key(
        settings.SECRET_KEY,
        salt,
        info_label,
    )

    try:

        payload = aes.encrypt(
            plaintext=plaintext,
            key=master,
        )

        return EncryptedSecret(
            ciphertext=payload.ciphertext,
            nonce=payload.nonce,
            tag=payload.tag,
            salt=_b64(salt),
        )

    except Exception as exc:
        raise EncryptionError(
            f"At-rest encryption failed: {exc}"
        ) from exc


def decrypt_secret(
    secret: EncryptedSecret,
    info_label: bytes = INFO_LABEL,
) -> bytes:
    """
    Unwrap a secret previously produced by :func:`encrypt_secret`.

    Raises:
        InvalidKeyError: the envelope is malformed or the
            integrity check failed.
    """

    settings = get_settings()

    try:

        salt = _unb64(secret.salt)

        master = _derive_master_key(
            settings.SECRET_KEY,
            salt,
            info_label,
        )

        payload = EncryptedPayload(
            nonce=secret.nonce,
            ciphertext=secret.ciphertext,
            tag=secret.tag,
        )

        return AESGCMCipher().decrypt(
            payload=payload,
            key=master,
        )

    except DecryptionError as exc:
        raise InvalidKeyError(
            f"At-rest decryption failed: {exc}"
        ) from exc

    except Exception as exc:
        raise InvalidKeyError(
            f"At-rest decryption failed: {exc}"
        ) from exc


def _derive_master_key(
    secret: str,
    salt: bytes,
    info_label: bytes,
) -> bytes:

    hkdf = HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        info=info_label,
    )

    return hkdf.derive(
        secret.encode()
    )


def _b64(raw: bytes) -> str:
    return base64.b64encode(raw).decode()


def _unb64(encoded: str) -> bytes:
    return base64.b64decode(encoded)
