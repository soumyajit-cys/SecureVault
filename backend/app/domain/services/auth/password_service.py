from passlib.context import CryptContext

from app.domain.services.password_service import (
    PasswordService,
)

pwd_context = CryptContext(
    schemes=["argon2"],
    deprecated="auto",
    argon2__memory_cost=102400,
    argon2__time_cost=3,
    argon2__parallelism=8,
)


class Argon2PasswordService(
    PasswordService
):

    def hash_password(
        self,
        password: str,
    ) -> str:

        return pwd_context.hash(
            password
        )

    def verify_password(
        self,
        password: str,
        password_hash: str,
    ) -> bool:

        return pwd_context.verify(
            password,
            password_hash,
        )