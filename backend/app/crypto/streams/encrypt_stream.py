from __future__ import annotations

from collections.abc import Generator, Iterable

from app.crypto.aes.aes_gcm import AESGCMCipher
from app.crypto.models.encrypted_payload import EncryptedPayload


class EncryptStream:
    """
    Encrypts a stream of plaintext chunks using a single AES session key.
    """

    def __init__(
        self,
        cipher: AESGCMCipher | None = None,
    ) -> None:

        self._cipher = cipher or AESGCMCipher()

    def encrypt(
        self,
        chunks: Iterable[bytes],
        key: bytes,
    ) -> Generator[EncryptedPayload, None, None]:
        """
        Encrypt each plaintext chunk independently.

        Yields:
            EncryptedPayload
        """

        for chunk in chunks:
            if not chunk:
                continue

            yield self._cipher.encrypt(
                plaintext=chunk,
                key=key,
            )