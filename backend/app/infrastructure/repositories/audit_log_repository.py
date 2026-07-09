from app.domain.models.audit_log import AuditLog
from app.infrastructure.repositories.base_repository import (
    SQLAlchemyRepository,
)


class SQLAlchemyAuditLogRepository(
    SQLAlchemyRepository[
        AuditLog
    ]
):
    model = AuditLog