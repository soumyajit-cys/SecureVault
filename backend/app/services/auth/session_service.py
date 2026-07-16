from app.infrastructure.repositories.session_repository import (
    SQLAlchemySessionRepository,
)
from app.services.auth.token_utils import (
    generate_session_id,
)


class SessionService:

    def __init__(
        self,
        repository: SQLAlchemySessionRepository,
    ):
        self.repository = repository

    def create_session_identifier(
        self,
    ) -> str:

        return generate_session_id()

    def revoke_session(
        self,
        session,
    ):

        session.revoked = True

        self.repository.update(
            session
        )