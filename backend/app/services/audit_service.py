import hashlib
from datetime import datetime
from datetime import timezone

from app.domain.models.audit_log import AuditLog

# Digest used to anchor the first entry of the chain.
GENESIS_PREV_HASH = "0" * 64


def chain_hash(
    prev_hash: str,
    created_at: datetime,
    user_id,
    action: str,
    details: str | None,
    resource_type: str | None,
    resource_id: str | None,
) -> str:
    """
    Deterministic SHA-256 over the full canonical
    payload of an entry plus the digest of the
    previous one. Any field change (including a
    forged chain link) yields a different digest.
    """

    canonical = "|".join(
        [
            prev_hash,
            _as_utc(created_at).isoformat(),
            str(user_id) if user_id else "",
            action,
            details or "",
            resource_type or "",
            resource_id or "",
        ]
    )

    return hashlib.sha256(
        canonical.encode("utf-8")
    ).hexdigest()


def _as_utc(value: datetime) -> datetime:
    """
    SQLite returns naive datetimes; normalise to
    timezone-aware UTC for hashing.
    """

    if value.tzinfo is None:
        return value.replace(
            tzinfo=timezone.utc
        )

    return value


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
    ) -> AuditLog:

        previous = (
            self.repository.last()
        )

        prev_hash = (
            previous.entry_hash
            if previous
            else GENESIS_PREV_HASH
        )

        created_at = datetime.now(timezone.utc)

        entry = AuditLog(
            user_id=user_id,
            action=action,
            details=details,
            resource_type=resource_type,
            resource_id=resource_id,
            prev_hash=prev_hash,
            entry_hash=GENESIS_PREV_HASH,
            created_at=created_at,
        )

        entry.entry_hash = chain_hash(
            prev_hash,
            created_at,
            user_id,
            action,
            details,
            resource_type,
            resource_id,
        )

        return self.repository.create(entry)

    def verify_chain(
        self,
    ) -> list[str]:
        """
        Replay the whole trail and report every
        inconsistency. An empty list means the log
        is untampered.
        """

        entries = (
            self.repository.list_all_unpaginated()
        )

        issues: list[str] = []

        expected_prev = GENESIS_PREV_HASH

        for entry in entries:

            if entry.prev_hash != expected_prev:
                issues.append(
                    f"{entry.id}: prev_hash mismatch"
                )

            recomputed = chain_hash(
                entry.prev_hash,
                entry.created_at,
                entry.user_id,
                entry.action,
                entry.details,
                entry.resource_type,
                entry.resource_id,
            )

            if recomputed != entry.entry_hash:
                issues.append(
                    f"{entry.id}: entry_hash mismatch"
                )

            expected_prev = entry.entry_hash

        return issues

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
