from app.crypto.argon2.kdf import (
    Argon2KDF,
)


def test_different_salts():

    kdf = Argon2KDF()

    key1 = (
        kdf.derive_key(
            "password",
            kdf.generate_salt(),
        )
    )

    key2 = (
        kdf.derive_key(
            "password",
            kdf.generate_salt(),
        )
    )

    assert key1 != key2