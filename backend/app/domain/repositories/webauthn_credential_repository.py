from abc import abstractmethod
from uuid import UUID

from app.domain.models.webauthn_credential import WebAuthnCredential
from app.domain.repositories.base import Repository


class WebAuthnCredentialRepository(
    Repository[WebAuthnCredential]
):

    @abstractmethod
    def list_for_user(
        self,
        user_id: UUID,
    ) -> list[WebAuthnCredential]:
        pass

    @abstractmethod
    def get_by_credential_id(
        self,
        credential_id: str,
    ) -> WebAuthnCredential | None:
        pass

    @abstractmethod
    def get_owned(
        self,
        user_id: UUID,
        credential_id: str,
    ) -> WebAuthnCredential | None:
        pass

    @abstractmethod
    def delete_for_user(
        self,
        user_id: UUID,
    ) -> int:
        pass
