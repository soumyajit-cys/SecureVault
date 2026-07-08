from abc import abstractmethod

from app.domain.models.refresh_token import RefreshToken
from app.domain.repositories.base import Repository


class RefreshTokenRepository(
    Repository[RefreshToken]
):

    @abstractmethod
    def get_by_token_hash(
        self,
        token_hash: str,
    ) -> RefreshToken | None:
        pass