from app.domain.models.refresh_token import (
    RefreshToken,
)
from app.infrastructure.repositories.base_repository import (
    SQLAlchemyRepository,
)

from sqlalchemy import select

from sqlalchemy import select

def get_by_family(
    self,
    family: str,
):

    stmt = (
        select(
            RefreshToken
        )
        .where(
            RefreshToken.token_family
            == family
        )
    )

    return (
        self.db.scalars(stmt)
        .all()
    )


def revoke_family(
    self,
    family: str,
):

    tokens = (
        self.get_by_family(
            family
        )
    )

    for token in tokens:
        token.revoked = True

    self.db.flush()

def get_active_by_hash(
    self,
    token_hash: str,
):

    stmt = (
        select(
            RefreshToken
        )
        .where(
            RefreshToken.token_hash
            == token_hash,
            RefreshToken.revoked.is_(False),
        )
    )

    return self.db.scalar(
        stmt
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
    

    