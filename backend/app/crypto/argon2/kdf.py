import os

from argon2.low_level import (
    Type,
    hash_secret_raw,
)

from app.crypto.interfaces.kdf import (
    KeyDerivationFunction,
)


class Argon2KDF(
    KeyDerivationFunction
):

    SALT_SIZE = 16

    KEY_SIZE = 32

    TIME_COST = 3

    MEMORY_COST = 102400

    PARALLELISM = 8

    def generate_salt(
        self,
    ) -> bytes:

        return os.urandom(
            self.SALT_SIZE
        )

    def derive_key(
        self,
        password: str,
        salt: bytes,
    ) -> bytes:

        return hash_secret_raw(
            secret=password.encode(),
            salt=salt,
            time_cost=self.TIME_COST,
            memory_cost=self.MEMORY_COST,
            parallelism=self.PARALLELISM,
            hash_len=self.KEY_SIZE,
            type=Type.ID,
        )

    def derive_key_with_new_salt(
        self,
        password: str,
    ) -> tuple[bytes, bytes]:

        salt = (
            self.generate_salt()
        )

        key = (
            self.derive_key(
                password,
                salt,
            )
        )

        return key, salt