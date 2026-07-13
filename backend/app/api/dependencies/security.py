from app.services.auth.password_service import (
    Argon2PasswordService,
)


def get_password_service():
    return Argon2PasswordService()