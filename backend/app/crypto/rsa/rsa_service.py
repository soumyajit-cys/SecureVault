from app.crypto.interfaces.asymmetric import (
    AsymmetricCipher,
)


class RSAService(
    AsymmetricCipher
):

    def generate_key_pair(
        self,
    ):
        raise NotImplementedError

    def encrypt(
        self,
        data: bytes,
        public_key: bytes,
    ):
        raise NotImplementedError

    def decrypt(
        self,
        data: bytes,
        private_key: bytes,
    ):
        raise NotImplementedError