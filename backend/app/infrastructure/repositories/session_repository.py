from app.domain.models.session import Session
from app.infrastructure.repositories.base_repository import (
    SQLAlchemyRepository,
)


class SQLAlchemySessionRepository(
    SQLAlchemyRepository[
        Session
    ]
):
    model = Session