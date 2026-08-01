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
        resource_type: str | None = None,
        resource_id: str | None = None,
    ):

        self.repository.create(
            AuditLog(
                user_id=user_id,
                action=action,
                details=details,
                resource_type=resource_type,
                resource_id=resource_id,
            )
        )

    def list_for_user(
        self,
        user_id,
        page: int = 1,
        page_size: int = 20,
        action: str | None = None,
    ) -> tuple[list[AuditLog], int]:

        return self.repository.list_for_user(
            user_id,
            page=page,
            page_size=page_size,
            action=action,
        )

    def list_all(
        self,
        page: int = 1,
        page_size: int = 20,
        action: str | None = None,
        user_id=None,
    ) -> tuple[list[AuditLog], int]:

        return self.repository.list_all(
            page=page,
            page_size=page_size,
            action=action,
            user_id=user_id,
        )