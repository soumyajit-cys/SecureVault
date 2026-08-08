from uuid import UUID

from app.core.exceptions import (
    QuotaExceededError,
)

from app.infrastructure.repositories.stored_file_repository import (
    SQLAlchemyStoredFileRepository,
)


class QuotaService:
    """
    Enforces per-user storage quotas based on the
    sum of encrypted bytes stored for active files.
    """

    def __init__(
        self,
        stored_files: SQLAlchemyStoredFileRepository,
    ) -> None:

        self.files = stored_files

    def usage(
        self,
        user_id: UUID,
    ) -> int:

        return (
            self.files
            .sum_active_size_for_user(user_id)
        )

    def check(
        self,
        user_id: UUID,
        quota_bytes: int | None,
        additional_bytes: int = 0,
    ) -> None:
        """
        Raise ``QuotaExceededError`` when adding
        ``additional_bytes`` would exceed the user's
        quota. ``None`` quota means unlimited.
        """

        if quota_bytes is None or quota_bytes <= 0:
            return

        current = self.usage(user_id)

        if (
            current + additional_bytes
            > quota_bytes
        ):
            raise QuotaExceededError(
                "Storage quota exceeded. "
                "Free up space or contact an "
                "administrator to raise your quota."
            )
