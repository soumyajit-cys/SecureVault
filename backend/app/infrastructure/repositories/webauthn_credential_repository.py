from uuid import UUID

from sqlalchemy import select

from app.domain.models.webauthn_credential import WebAuthnCredential
from app.infrastructure.repositories.base_repository import (
    SQLAlchemyRepository,
)


class SQLAlchemyWebAuthnCredentialRepository(
    SQLAlchemyRepository[WebAuthnCredential]
):
    model = WebAuthnCredential

    def list_for_user(
        self,
        user_id: UUID,
    ) -> list[WebAuthnCredential]:

        stmt = (
            select(WebAuthnCredential)
            .where(
                WebAuthnCredential.user_id
                == user_id
            )
            .order_by(
                WebAuthnCredential.created_at.desc()
            )
        )

        return list(
            self.db.scalars(stmt).all()
        )

    def get_by_credential_id(
        self,
        credential_id: str,
    ) -> WebAuthnCredential | None:

        stmt = (
            select(WebAuthnCredential)
            .where(
                WebAuthnCredential.credential_id
                == credential_id
            )
            .limit(1)
        )

        return self.db.scalar(stmt)

    def get_owned(
        self,
        user_id: UUID,
        credential_id: str,
    ) -> WebAuthnCredential | None:

        stmt = (
            select(WebAuthnCredential)
            .where(
                WebAuthnCredential.user_id
                == user_id,
                WebAuthnCredential.credential_id
                == credential_id,
            )
            .limit(1)
        )

        return self.db.scalar(stmt)

    def delete_for_user(
        self,
        user_id: UUID,
    ) -> int:

        result = self.db.query(
            WebAuthnCredential
        ).filter(
            WebAuthnCredential.user_id
            == user_id
        ).delete()

        return result or 0
