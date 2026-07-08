from app.domain.models.session import Session
from app.domain.repositories.base import Repository


class SessionRepository(
    Repository[Session]
):
    pass