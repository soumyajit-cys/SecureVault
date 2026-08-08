from datetime import UTC
from datetime import datetime
from datetime import timedelta

from app.core.config import get_settings
from app.core.logging import get_logger

settings = get_settings()

logger = get_logger(__name__)


class DataRetentionService:
    """
    Deletes stale rows across the security tables
    (audit trail, sessions, refresh tokens, one-time
    tokens) once they pass the retention window.
    Active sessions and tokens are never touched.
    """

    def __init__(
        self,
        audit_repository,
        session_repository,
        refresh_repository,
        password_reset_repository,
        verification_repository,
    ) -> None:

        self.audit = audit_repository

        self.sessions = session_repository

        self.refresh = refresh_repository

        self.reset_tokens = password_reset_repository

        self.verify_tokens = verification_repository

    def run(
        self,
        retention_days: int | None = None,
    ) -> dict:
        """
        Purge everything older than the retention
        window. Returns per-table counters.
        """

        days = (
            retention_days
            or settings.DATA_RETENTION_DAYS
        )

        cutoff = datetime.now(UTC) - timedelta(
            days=days
        )

        summary = {
            "audit_logs": self.audit.purge_older_than(
                cutoff
            ),
            "sessions": self.sessions.purge_older_than(
                cutoff
            ),
            "refresh_tokens": self.refresh.purge_older_than(
                cutoff
            ),
            "password_reset_tokens": (
                self.reset_tokens.purge_older_than(
                    cutoff
                )
            ),
            "email_verification_tokens": (
                self.verify_tokens.purge_older_than(
                    cutoff
                )
            ),
        }

        logger.info(
            "retention_purge_completed",
            **summary,
        )

        return summary
