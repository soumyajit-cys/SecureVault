from __future__ import annotations

from abc import ABC
from abc import abstractmethod


class SymmetricCipher(ABC):

    @abstractmethod
    def encrypt(
        self,
        plaintext: bytes,
        key: bytes,
    ):
        """
        Encrypt plaintext using the supplied key.
        """
        raise NotImplementedError

    @abstractmethod
    def decrypt(
        self,
        ciphertext: bytes,
        nonce: bytes,
        tag: bytes,
        key: bytes,
    ) -> bytes:
        """
        Decrypt ciphertext using the supplied key.
        """
        raise NotImplementedError