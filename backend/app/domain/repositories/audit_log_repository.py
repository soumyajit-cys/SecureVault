from app.domain.models.audit_log import AuditLog
from app.domain.repositories.base import Repository


class AuditLogRepository(
    Repository[AuditLog]
):
    pass