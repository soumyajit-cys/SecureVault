from __future__ import annotations

from abc import ABC, abstractmethod
from contextlib import contextmanager
from typing import BinaryIO, Iterable, Iterator


class ObjectStore(ABC):
    """
    Raw bytes-in/bytes-out for committed encrypted containers.

    Keys are opaque, slash-separated, traversal-free strings
    (e.g. ``files/<user_id>/<file_id>.svlt``) — the same shape
    as the ``storage_path`` values already persisted in the
    database, so rows stay valid across backends.

    Everything is streaming: readers and writers must work
    with bounded memory regardless of object size. The crypto
    layer above (container format, AES-GCM, RSA wrap) is
    untouched — it just reads/writes different streams.
    """

    # -------------------------------------------------
    # Writes
    # -------------------------------------------------

    @abstractmethod
    def write(
        self,
        key: str,
    ):
        """
        Open a writable binary stream for ``key``.

        Returns a context manager yielding the stream;
        closing commits the object, raising inside the
        block aborts it (no partial object is left).
        """

    def put(
        self,
        key: str,
        stream: BinaryIO,
        chunk_size: int = 1024 * 1024,
    ) -> int:
        """
        Store the full contents of ``stream`` under ``key``.

        Streams in ``chunk_size`` blocks; returns bytes written.
        """

        written = 0

        with self.write(key) as out:

            while True:

                chunk = stream.read(chunk_size)

                if not chunk:
                    break

                out.write(chunk)

                written += len(chunk)

        return written

    # -------------------------------------------------
    # Reads
    # -------------------------------------------------

    @abstractmethod
    def open(
        self,
        key: str,
    ) -> BinaryIO:
        """
        Open a readable binary stream for ``key``.

        Reads sequentially with bounded memory. The caller
        owns the stream and must close it. Raises
        ``NotFoundError`` when the key does not exist.
        """

    @abstractmethod
    def exists(
        self,
        key: str,
    ) -> bool:
        ...

    @abstractmethod
    def size(
        self,
        key: str,
    ) -> int | None:
        """
        Object size in bytes, or None when missing.
        """

    # -------------------------------------------------
    # Delete / list
    # -------------------------------------------------

    @abstractmethod
    def delete(
        self,
        key: str,
    ) -> bool:
        """
        Delete ``key``. Returns True when something was removed.
        """

    @abstractmethod
    def iter_keys(
        self,
        prefix: str = "",
    ) -> Iterable[str]:
        """
        Yield every key starting with ``prefix``.
        """


@contextmanager
def closing_reader(
    stream: BinaryIO,
) -> Iterator[BinaryIO]:
    """
    Ensure a store-opened stream is closed after use.
    """

    try:

        yield stream

    finally:

        try:

            stream.close()

        except Exception:

            pass
