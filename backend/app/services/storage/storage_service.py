from __future__ import annotations

import shutil
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import BinaryIO, Iterable

from app.core.config import get_settings
from app.core.exceptions import NotFoundError
from app.domain.models.stored_file import StoredFile
from app.infrastructure.storage.object_store import ObjectStore

settings = get_settings()


class StoragePathError(Exception):
    """Raised when a storage path cannot be resolved safely."""


class StorageService:
    """
    Manages the secure storage layout and committed containers.

    Two kinds of bytes live here:

    - **Committed containers** (``files/<user>/<file>.svlt``) go
      through the configured :class:`ObjectStore` — local disk
      by default, or any S3-compatible bucket when
      ``STORAGE_BACKEND=s3``. The key format is identical to
      the historical relative path, so database rows stay
      valid across backends.
    - **Ephemeral scratch** (``tmp/`` staged uploads,
      ``vault/`` restore dirs) always stays on local disk:
      it is per-request transient and never needs persistence.

    The historical path-based API below is unchanged, so
    local-mode behavior (and its tests) are untouched.
    """

    def __init__(
        self,
        storage_dir: str | Path | None = None,
        *,
        backend: str | None = None,
        object_store: ObjectStore | None = None,
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

        from app.infrastructure.storage.factory import (
            build_object_store,
        )

        self.backend = (
            backend
            or settings.STORAGE_BACKEND
            or "local"
        ).lower()

        self._store: ObjectStore = (
            object_store
            or build_object_store(
                settings,
                root=self.files_dir,
                backend=self.backend,
            )
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

    # -------------------------------------------------
    # Committed Containers (backend-agnostic)
    # -------------------------------------------------
    #
    # These methods route through the configured
    # ObjectStore (local disk or S3) and work with
    # streams, so memory stays flat for arbitrary file
    # sizes. Keys use the same ``files/<user>/<file>.svlt``
    # shape as the historical relative paths, so stored
    # ``storage_path`` values are valid in both backends.

    def container_key(
        self,
        user_id: uuid.UUID,
        file_id: uuid.UUID,
    ) -> str:
        """
        Object key for an encrypted container.
        """

        return (
            f"files/{user_id}/{file_id}.svlt"
        )

    def write_container(
        self,
        key: str,
    ):
        """
        Open a streaming writer for a container object.

        Returns a context manager yielding a binary stream;
        closing commits, raising aborts (no partial object).
        """

        return self._store.write(key)

    def put_container(
        self,
        key: str,
        stream: BinaryIO,
        chunk_size: int = 1024 * 1024,
    ) -> int:
        """
        Store ``stream`` as a container object. Streams in
        blocks; returns bytes written.
        """

        return self._store.put(
            key,
            stream,
            chunk_size=chunk_size,
        )

    def open_container(
        self,
        key: str,
    ) -> BinaryIO:
        """
        Open a streaming reader for a container object.

        The caller owns the stream and must close it.
        Raises NotFoundError when the key does not exist.
        """

        return self._store.open(key)

    def container_exists(
        self,
        key: str,
    ) -> bool:

        return self._store.exists(key)

    def container_size(
        self,
        key: str,
    ) -> int | None:

        return self._store.size(key)

    def delete_container(
        self,
        key: str,
    ) -> bool:
        """
        Delete a container object by key. Returns True when
        something was removed. (Compare ``remove_container``,
        which takes a StoredFile record and resolves its path
        through the local layout.)
        """

        return self._store.delete(key)

    def iter_container_keys(
        self,
        prefix: str = "files/",
    ) -> Iterable[str]:
        """
        Yield every committed-container key.
        """

        return self._store.iter_keys(prefix)
