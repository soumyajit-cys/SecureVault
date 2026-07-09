from app.domain.models.refresh_token import (
    RefreshToken,
)
from app.infrastructure.repositories.base_repository import (
    SQLAlchemyRepository,
)


class SQLAlchemyRefreshTokenRepository(
    SQLAlchemyRepository[
        RefreshToken
    ]
):
    model = RefreshToken

    def get_by_token_hash(
        self,
        token_hash: str,
    ) -> RefreshToken | None:
        return (
            self.db.query(
                RefreshToken
            )
            .filter(
                RefreshToken.token_hash
                == token_hash
            )
            .first()
        )