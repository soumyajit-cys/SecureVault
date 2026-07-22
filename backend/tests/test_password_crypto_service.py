from app.services.password_crypto_service import (
    PasswordCryptoService,
)


def test_password_encrypt_decrypt():

    service = (
        PasswordCryptoService()
    )

    encrypted = (
        service.encrypt(
            "SecureVault Secret",
            "StrongPassword#2026",
        )
    )

    decrypted = (
        service.decrypt(
            encrypted["payload"],
            "StrongPassword#2026",
            encrypted["salt"],
        )
    )

    assert (
        decrypted
        == "SecureVault Secret"
    )