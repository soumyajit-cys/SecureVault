from app.crypto.interfaces.kdf import (
    KeyDerivationFunction,
)


class Argon2KDF(
    KeyDerivationFunction
):

    def derive_key(
        self,
        password: str,
        salt: bytes,
    ) -> bytes:
        raise NotImplementedError