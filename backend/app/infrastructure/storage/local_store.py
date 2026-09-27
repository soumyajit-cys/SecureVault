from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from typing import BinaryIO, Iterable, Iterator

from app.core.exceptions import NotFoundError
from app.infrastructure.storage.object_store import ObjectStore


def _validate_key(key: str) -> str:
    """
    Reject absolute keys and ``..`` segments so a key can
    never escape the store root.
    """

    if not key or key.startswith("/") or ".." in key.split("/"):
        raise ValueError(f"Unsafe object key: {key!r}")

    return key


class LocalObjectStore(ObjectStore):
    """
    ObjectStore over a local directory (the current behavior).

    ``key`` maps to ``<root>/<key>`` as a file path.
    """

    def __init__(
        self,
        root: str | Path,
    ) -> None:

        self.root = Path(root)

    # -------------------------------------------------
    # Writes
    # -------------------------------------------------

    @contextmanager
    def write(
        self,
        key: str,
    ) -> Iterator[BinaryIO]:

        _validate_key(key)

        target = self.root / key

        target.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        stream = target.open("wb")

        try:

            yield stream

        except Exception:

            stream.close()

            target.unlink(missing_ok=True)

            raise

        else:

            stream.close()

    # -------------------------------------------------
    # Reads
    # -------------------------------------------------

    def open(
        self,
        key: str,
    ) -> BinaryIO:

        _validate_key(key)

        target = self.root / key

        if not target.is_file():
            raise NotFoundError(
                f"Object not found: {key}"
            )

        return target.open("rb")

    def exists(
        self,
        key: str,
    ) -> bool:

        _validate_key(key)

        return (self.root / key).is_file()

    def size(
        self,
        key: str,
    ) -> int | None:

        _validate_key(key)

        target = self.root / key

        if not target.is_file():
            return None

        return target.stat().st_size

    # -------------------------------------------------
    # Delete / list
    # -------------------------------------------------

    def delete(
        self,
        key: str,
    ) -> bool:

        _validate_key(key)

        target = self.root / key

        if target.is_file():
            target.unlink(missing_ok=True)
            return True

        return False

    def iter_keys(
        self,
        prefix: str = "",
    ) -> Iterable[str]:

        if not self.root.is_dir():
            return

        for path in sorted(self.root.rglob("*")):

            if not path.is_file():
                continue

            key = path.relative_to(self.root).as_posix()

            if key.startswith(prefix):
                yield key
