from app.services.auth.password_policy import (
    PasswordPolicy,
)


def test_valid_password():

    result = (
        PasswordPolicy.validate(
            "SecureVault#2026"
        )
    )

    assert result.valid is True


def test_missing_uppercase():

    result = (
        PasswordPolicy.validate(
            "securevault#2026"
        )
    )

    assert result.valid is False


def test_missing_special():

    result = (
        PasswordPolicy.validate(
            "SecureVault2026"
        )
    )

    assert result.valid is False