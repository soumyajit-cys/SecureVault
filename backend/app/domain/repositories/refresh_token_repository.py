from abc import abstractmethod

from app.domain.models.refresh_token import RefreshToken
from app.domain.repositories.base import Repository

from abc import abstractmethod


@abstractmethod
def get_by_family(
    self,
    family: str,
):
    pass


@abstractmethod
def revoke_family(
    self,
    family: str,
):
    pass

class RefreshTokenRepository(
    Repository[RefreshToken]
):

    @abstractmethod
    def get_by_token_hash(
        self,
        token_hash: str,
    ) -> RefreshToken | None:
        pass

 

 