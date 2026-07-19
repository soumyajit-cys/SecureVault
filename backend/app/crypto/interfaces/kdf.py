from abc import ABC
from abc import abstractmethod


class KeyDerivationFunction(
    ABC
):

    @abstractmethod
    def derive_key(
        self,
        password: str,
        salt: bytes,
    ) -> bytes:
        raise NotImplementedError