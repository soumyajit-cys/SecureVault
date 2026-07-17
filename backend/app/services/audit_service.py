from app.domain.models.audit_log import AuditLog


class AuditService:

    def __init__(
        self,
        repository,
    ):
        self.repository = repository

    def log(
        self,
        user_id,
        action: str,
        details: str | None = None,
    ):

        self.repository.create(
            AuditLog(
                user_id=user_id,
                action=action,
                details=details,
            )
        )