from datetime import datetime
from uuid import UUID

from sqlalchemy import func
from sqlalchemy import or_
from sqlalchemy import select

from app.domain.models.stored_file import StoredFile
from app.infrastructure.repositories.base_repository import (
    SQLAlchemyRepository,
)


class SQLAlchemyStoredFileRepository(
    SQLAlchemyRepository[StoredFile]
):
    model = StoredFile

    def get_for_user(
        self,
        user_id: UUID,
        file_id: UUID,
        include_deleted: bool = False,
    ) -> StoredFile | None:

        stmt = (
            select(self.model)
            .where(
                self.model.id == file_id,
                self.model.user_id == user_id,
            )
        )

        if not include_deleted:
            stmt = stmt.where(
                self.model.status == "active"
            )

        return self.db.scalar(stmt)

    def get_by_idempotency_key(
        self,
        user_id: UUID,
        idempotency_key: str,
    ) -> StoredFile | None:

        stmt = (
            select(self.model)
            .where(
                self.model.user_id == user_id,
                self.model.idempotency_key
                == idempotency_key,
                self.model.status == "active",
            )
            .order_by(
                self.model.created_at.desc()
            )
            .limit(1)
        )

        return self.db.scalar(stmt)

    def list_for_user(
        self,
        user_id: UUID,
        page: int,
        page_size: int,
        status: str | None = None,
        mime_type: str | None = None,
        is_folder: bool | None = None,
        search: str | None = None,
    ) -> tuple[list[StoredFile], int]:

        filters = [
            self.model.user_id == user_id,
        ]

        if status:
            filters.append(
                self.model.status == status
            )

        if mime_type:
            filters.append(
                self.model.mime_type == mime_type
            )

        if is_folder is not None:
            filters.append(
                self.model.is_folder == is_folder
            )

        if search:
            filters.append(
                self._search_filter(search)
            )

        total = (
            self.db.scalar(
                select(func.count(self.model.id))
                .where(*filters)
            )
            or 0
        )

        stmt = (
            select(self.model)
            .where(*filters)
            .order_by(
                self.model.created_at.desc(),
                self.model.id.desc(),
            )
            .offset((page - 1) * page_size)
            .limit(page_size)
        )

        items = list(
            self.db.scalars(stmt).all()
        )

        return items, total

    def get_by_storage_path(
        self,
        storage_path: str,
    ) -> StoredFile | None:

        stmt = (
            select(self.model)
            .where(
                self.model.storage_path == storage_path
            )
        )

        return self.db.scalar(stmt)
    def get_deleted_before(
        self,
        before: datetime,
    ) -> list[StoredFile]:

        stmt = (
            select(self.model)
            .where(
                self.model.status == "deleted",
                self.model.deleted_at.is_not(None),
                self.model.deleted_at < before,
            )
        )

        return list(
            self.db.scalars(stmt).all()
        )

    def _search_filter(
        self,
        search: str,
    ):
        """
        Search wider fields (filename, MIME type) with
        every whitespace-separated token required to
        match somewhere. Postgres can serve the ILIKE
        patterns from the pg_trgm GIN index; SQLite
        falls back to a plain scan.
        """

        from sqlalchemy import or_

        tokens = [
            token
            for token in (
                search.split()
            )
            if token
        ]

        clauses = []

        for token in tokens:

            pattern = f"%{token}%"

            clauses.append(
                or_(
                    self.model.original_filename.ilike(
                        pattern
                    ),
                    self.model.mime_type.ilike(
                        pattern
                    ),
                )
            )

        if len(clauses) == 1:
            return clauses[0]

        from sqlalchemy import and_

        return and_(*clauses)

    def get_all_active(
        self,
    ) -> list[StoredFile]:

        stmt = (
            select(self.model)
            .where(
                self.model.status == "active"
            )
        )

        return list(
            self.db.scalars(stmt).all()
        )

    def soft_delete(
        self,
        file: StoredFile,
        deleted_at: datetime,
    ) -> StoredFile:

        file.status = "deleted"

        file.deleted_at = deleted_at

        return self.update(file)

    def count_active_for_user(
        self,
        user_id: UUID,
    ) -> int:

        stmt = (
            select(func.count(self.model.id))
            .where(
                self.model.user_id == user_id,
                self.model.status == "active",
            )
        )

        return self.db.scalar(stmt) or 0

    def sum_active_size_for_user(
        self,
        user_id: UUID,
    ) -> int:
        """
        Total encrypted bytes currently stored for a user
        (active files only). Used for quota accounting.
        """

        stmt = (
            select(
                func.coalesce(
                    func.sum(
                        self.model.encrypted_size
                    ),
                    0,
                )
            )
            .where(
                self.model.user_id == user_id,
                self.model.status == "active",
            )
        )

        return int(self.db.scalar(stmt) or 0)
