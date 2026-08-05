from datetime import datetime
from datetime import timezone
from uuid import UUID

from sqlalchemy import func
from sqlalchemy import select

from app.domain.models.mfa_recovery_code import MfaRecoveryCode
from app.infrastructure.repositories.base_repository import (
    SQLAlchemyRepository,
)


class SQLAlchemyMfaRecoveryCodeRepository(
    SQLAlchemyRepository[MfaRecoveryCode]
):
    model = MfaRecoveryCode

    def count_available(
        self,
        user_id: UUID,
    ) -> int:

        stmt = (
            select(func.count(MfaRecoveryCode.id))
            .where(
                MfaRecoveryCode.user_id
                == user_id,
                MfaRecoveryCode.used_at.is_(None),
            )
        )

        return self.db.scalar(stmt) or 0

    def find_unused_by_hash(
        self,
        user_id: UUID,
        code_hash: str,
    ) -> MfaRecoveryCode | None:

        stmt = (
            select(MfaRecoveryCode)
            .where(
                MfaRecoveryCode.user_id
                == user_id,
                MfaRecoveryCode.code_hash
                == code_hash,
                MfaRecoveryCode.used_at.is_(None),
            )
            .limit(1)
        )

        return self.db.scalar(stmt)

    def mark_used(
        self,
        code: MfaRecoveryCode,
    ) -> None:

        code.used_at = datetime.now(timezone.utc)
        self.db.flush()

    def delete_all_for_user(
        self,
        user_id: UUID,
    ) -> None:

        self.db.query(MfaRecoveryCode).filter(
            MfaRecoveryCode.user_id == user_id
        ).delete()
