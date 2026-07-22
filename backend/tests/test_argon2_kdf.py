from app.crypto.argon2.kdf import (
    Argon2KDF,
)


def test_key_derivation():

    kdf = Argon2KDF()

    salt = (
        kdf.generate_salt()
    )

    key = (
        kdf.derive_key(
            "SecureVault#2026",
            salt,
        )
    )

    assert len(key) == 32