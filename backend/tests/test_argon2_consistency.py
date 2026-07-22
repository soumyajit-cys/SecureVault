from app.crypto.argon2.kdf import (
    Argon2KDF,
)


def test_same_password_same_salt():

    kdf = Argon2KDF()

    salt = (
        kdf.generate_salt()
    )

    key1 = (
        kdf.derive_key(
            "password",
            salt,
        )
    )

    key2 = (
        kdf.derive_key(
            "password",
            salt,
        )
    )

    assert key1 == key2