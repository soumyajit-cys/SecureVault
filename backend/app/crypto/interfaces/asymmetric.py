from abc import ABC
from abc import abstractmethod


class AsymmetricCipher(
    ABC
):

    @abstractmethod
    def generate_key_pair(
        self,
    ):
        raise NotImplementedError

    @abstractmethod
    def encrypt(
        self,
        data: bytes,
        public_key: bytes,
    ):
        raise NotImplementedError

    @abstractmethod
    def decrypt(
        self,
        data: bytes,
        private_key: bytes,
    ):
        raise NotImplementedError