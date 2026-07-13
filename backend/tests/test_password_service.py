from app.services.auth.password_service import (
    Argon2PasswordService,
)


def test_hash_password():

    service = (
        Argon2PasswordService()
    )

    password = (
        "SecureVault#2026"
    )

    password_hash = (
        service.hash_password(
            password
        )
    )

    assert (
        password_hash
        != password
    )


def test_verify_password():

    service = (
        Argon2PasswordService()
    )

    password = (
        "SecureVault#2026"
    )

    password_hash = (
        service.hash_password(
            password
        )
    )

    assert service.verify_password(
        password,
        password_hash,
    )


def test_invalid_password():

    service = (
        Argon2PasswordService()
    )

    password_hash = (
        service.hash_password(
            "SecureVault#2026"
        )
    )

    assert (
        service.verify_password(
            "WrongPassword",
            password_hash,
        )
        is False
    )