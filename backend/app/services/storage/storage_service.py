from __future__ import annotations

import shutil
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path

from app.core.config import get_settings
from app.domain.models.stored_file import StoredFile

settings = get_settings()


class StoragePathError(Exception):
    """Raised when a storage path cannot be resolved safely."""


class StorageService:
    """
    Manages the on-disk secure storage layout.

    Layout
    ------

    ::

        <STORAGE_DIR>/
        ├── tmp/                      # staged uploads
        │   └── <uuid>.part
        ├── files/                    # committed encrypted containers
        │   └── <user_id>/
        │       └── <file_id>.svlt
        └── vault/                    # exported/restored material
            └── <uuid>/

    Every path is derived exclusively from UUIDs, never from user
    supplied names, so path traversal is impossible by design.
    """

    def __init__(
        self,
        storage_dir: str | Path | None = None,
    ) -> None:

        self.root = Path(
            storage_dir
            or settings.STORAGE_DIR
        )

        self.files_dir = (
            self.root / "files"
        )

        self.temp_dir = (
            self.root / "tmp"
        )

        self.vault_dir = (
            self.root / "vault"
        )

        self.ensure_layout()

    # -------------------------------------------------
    # Layout
    # -------------------------------------------------

    def ensure_layout(self) -> None:
        """
        Create the storage directory structure if missing.
        """

        for directory in (
            self.files_dir,
            self.temp_dir,
            self.vault_dir,
        ):

            directory.mkdir(
                parents=True,
                exist_ok=True,
            )

    # -------------------------------------------------
    # Container Paths
    # -------------------------------------------------

    def container_path(
        self,
        user_id: uuid.UUID,
        file_id: uuid.UUID,
    ) -> Path:
        """
        Resolve the absolute path of an encrypted container.

        The path is built from UUIDs only.
        """

        directory = self.user_dir(
            user_id
        )

        return directory / f"{file_id}.svlt"

    def user_dir(
        self,
        user_id: uuid.UUID,
    ) -> Path:
        """
        Per-user storage directory.
        """

        directory = self.files_dir / str(
            user_id
        )

        directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        return directory

    def relative_path(
        self,
        path: Path,
    ) -> str:
        """
        Convert an absolute storage path to its relative form
        for persistence in the database.
        """

        try:

            return (
                path.resolve()
                .relative_to(
                    self.root.resolve()
                )
                .as_posix()
            )

        except ValueError as exc:
            raise StoragePathError(
                "Path is outside the storage root."
            ) from exc

    def resolve_path(
        self,
        storage_path: str,
    ) -> Path:
        """
        Convert a stored relative path back to an absolute path,
        rejecting any traversal outside the storage root.
        """

        candidate = (
            self.root / storage_path
        ).resolve()

        if not str(candidate).startswith(
            str(self.root.resolve())
        ):

            raise StoragePathError(
                "Unsafe storage path."
            )

        return candidate

    # -------------------------------------------------
    # Temporary Files
    # -------------------------------------------------

    def create_temp_path(
        self,
        suffix: str = ".part",
    ) -> Path:
        """
        Allocate a unique staged-upload path.
        """

        return (
            self.temp_dir
            / f"{uuid.uuid4().hex}{suffix}"
        )

    def vault_dir_for(
        self,
        identifier: str | None = None,
    ) -> Path:
        """
        Allocate a unique directory for exported/restored material.
        """

        directory = (
            self.vault_dir
            / (identifier or uuid.uuid4().hex)
        )

        directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        return directory

    # -------------------------------------------------
    # Cleanup
    # -------------------------------------------------

    def remove(
        self,
        path: str | Path,
    ) -> bool:
        """
        Remove a file or directory from storage.

        Returns True when something was removed.
        """

        target = Path(path)

        if target.is_file():

            target.unlink(
                missing_ok=True
            )

            return True

        if target.is_dir():

            shutil.rmtree(
                target,
                ignore_errors=True,
            )

            return True

        return False

    def remove_container(
        self,
        stored_file: StoredFile,
    ) -> bool:
        """
        Remove the encrypted container for a stored file record.
        """

        path = self.resolve_path(
            stored_file.storage_path
        )

        return self.remove(path)

    def remove_temp_files_older_than(
        self,
        max_age_hours: int,
    ) -> int:
        """
        Delete staged uploads older than the given age.

        Returns the number of removed files.
        """

        cutoff = datetime.now(UTC) - timedelta(
            hours=max_age_hours
        )

        removed = 0

        for temp in self.temp_dir.iterdir():

            if not temp.is_file():
                continue

            mtime = datetime.fromtimestamp(
                temp.stat().st_mtime,
                tz=UTC,
            )

            if mtime < cutoff:

                temp.unlink(
                    missing_ok=True
                )

                removed += 1

        return removed

    def iter_containers(
        self,
    ):
        """
        Yield every encrypted container under the files layout.
        """

        for user_dir in (
            self.files_dir.iterdir()
        ):

            if not user_dir.is_dir():
                continue

            for container in (
                user_dir.iterdir()
            ):

                if (
                    container.is_file()
                    and container.suffix == ".svlt"
                ):

                    yield container

    def storage_usage_bytes(
        self,
    ) -> int:
        """
        Total bytes used by committed containers.
        """

        total = 0

        for container in (
            self.iter_containers()
        ):

            total += container.stat().st_size

        return total
