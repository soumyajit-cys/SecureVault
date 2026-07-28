from __future__ import annotations

from collections.abc import Generator, Iterable

from app.crypto.aes.aes_gcm import AESGCMCipher
from app.crypto.models.encrypted_payload import EncryptedPayload


class DecryptStream:
    """
    Decrypts a stream of encrypted chunks.
    """

    def __init__(
        self,
        cipher: AESGCMCipher | None = None,
    ) -> None:

        self._cipher = cipher or AESGCMCipher()

    def decrypt(
        self,
        payloads: Iterable[EncryptedPayload],
        key: bytes,
    ) -> Generator[bytes, None, None]:
        """
        Decrypt encrypted payloads lazily.
        """

        for payload in payloads:
            yield self._cipher.decrypt(
                payload=payload,
                key=key,
            )