from __future__ import annotations

from pathlib import Path
from typing import Generator

from .constants import DEFAULT_CHUNK_SIZE


class ChunkReader:
    """
    Reads a file lazily in fixed-size chunks.

    Memory usage remains constant regardless of file size.
    """

    def __init__(
        self,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
    ) -> None:

        self.chunk_size = chunk_size

    def read(
        self,
        path: str | Path,
    ) -> Generator[bytes, None, None]:

        file_path = Path(path)

        with file_path.open("rb") as stream:

            while True:

                chunk = stream.read(
                    self.chunk_size
                )

                if not chunk:
                    break

                yield chunk