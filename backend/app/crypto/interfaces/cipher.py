from abc import ABC
from abc import abstractmethod


class SymmetricCipher(ABC):

    @abstractmethod
    def encrypt(
        self,
        plaintext: bytes,
        key: bytes,
    ) -> bytes:
        raise NotImplementedError

    @abstractmethod
    def decrypt(
        self,
        ciphertext: bytes,
        key: bytes,
    ) -> bytes:
        raise NotImplementedError