from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime, timedelta

from app.core.config import get_settings
from app.domain.models.stored_file import StoredFile
from app.domain.repositories.stored_file_repository import (
    StoredFileRepository,
)
from app.services.storage.storage_service import (
    StorageService,
)

logger = logging.getLogger(__name__)

settings = get_settings()


class GarbageCollector:
    """
    Reconciles the database and the storage layout.

    Responsibilities:

    - remove orphaned containers (on disk, no record)
    - remove records whose container is missing
    - purge soft-deleted files after the retention window
    - clean up stale staged uploads

    ``run_all`` returns a summary dict and is safe to call
    periodically from the cleanup task.
    """

    def __init__(
        self,
        storage: StorageService,
        stored_files: StoredFileRepository,
    ) -> None:

        self._storage = storage

        self._files = stored_files

    def run_all(
        self,
        temp_max_age_hours: int | None = None,
        retention_days: int | None = None,
    ) -> dict:
        """
        Execute every cleanup pass.

        Args:
            temp_max_age_hours: age after which staged uploads are
                removed (defaults to settings).
            retention_days: age after which soft-deleted records are
                purged (defaults to settings).

        Returns:
            Summary dict with per-pass counters.
        """

        temp_max_age = (
            temp_max_age_hours
            or settings.TEMP_FILE_MAX_AGE_HOURS
        )

        retention = (
            retention_days
            or settings.KEY_RETENTION_DAYS
        )

        orphaned = self.collect_orphans()

        missing = self.collect_missing_records()

        purged = self.purge_deleted(
            retention
        )

        temps = self.cleanup_temp_files(
            temp_max_age
        )

        summary = {
            "orphaned_containers": orphaned,
            "missing_records": missing,
            "purged_deleted": purged,
            "temp_files": temps,
        }

        logger.info(
            "Garbage collection completed: %s",
            summary,
        )

        return summary

    # -------------------------------------------------
    # Passes
    # -------------------------------------------------

    def collect_orphans(
        self,
    ) -> int:
        """
        Delete containers on disk that have no database record.

        Returns the number of removed containers.
        """

        known = {
            file.storage_path
            for file in self._files.get_all_active()
        }

        removed = 0

        for container in (
            self._storage.iter_containers()
        ):

            relative = self._storage.relative_path(
                container
            )

            if relative in known:
                continue

            self._storage.remove(container)

            removed += 1

        return removed

    def collect_missing_records(
        self,
    ) -> int:
        """
        Mark records whose container is missing on disk as deleted.

        Returns the number of updated records.
        """

        missing = 0

        for file in (
            self._files.get_all_active()
        ):

            path = self._storage.resolve_path(
                file.storage_path
            )

            if path.is_file():
                continue

            self._files.soft_delete(
                file,
                datetime.now(UTC),
            )

            missing += 1

        return missing

    def purge_deleted(
        self,
        retention_days: int,
    ) -> int:
        """
        Purge soft-deleted records and their containers.

        Returns the number of purged records.
        """

        cutoff = datetime.now(UTC) - timedelta(
            days=retention_days
        )

        purged = 0

        for file in (
            self._files.get_deleted_before(
                cutoff
            )
        ):

            self._storage.remove_container(
                file
            )

            self._files.delete(file)

            purged += 1

        return purged

    def cleanup_temp_files(
        self,
        max_age_hours: int,
    ) -> int:
        """
        Remove staged uploads older than the given age.

        Returns the number of removed files.
        """

        return self._storage.remove_temp_files_older_than(
            max_age_hours
        )


class CleanupTask:
    """
    Periodically runs the garbage collector.

    Used by the application lifespan; safe to start and stop.
    """

    def __init__(
        self,
        collector: GarbageCollector,
        interval_hours: int | None = None,
    ) -> None:

        self._collector = collector

        self._interval_seconds = (
            (interval_hours or settings.GARBAGE_COLLECTION_INTERVAL_HOURS)
            * 3600
        )

        self._task: asyncio.Task | None = None

    def start(self) -> None:
        """
        Start the background loop if not already running.
        """

        if self._task is None:

            self._task = asyncio.create_task(
                self._loop()
            )

    async def stop(self) -> None:
        """
        Stop the background loop.
        """

        if self._task is not None:

            self._task.cancel()

            try:

                await self._task

            except asyncio.CancelledError:
                pass

            self._task = None

    async def run_now(self) -> dict:
        """
        Trigger a single collection pass (for tests and admins).
        """

        return self._collector.run_all()

    async def _loop(self) -> None:
        """
        Background loop; calls the collector on an interval.
        """

        while True:

            try:

                self._collector.run_all()

            except Exception as exc:

                logger.exception(
                    "Garbage collection failed: %s",
                    exc,
                )

            await asyncio.sleep(
                self._interval_seconds
            )
