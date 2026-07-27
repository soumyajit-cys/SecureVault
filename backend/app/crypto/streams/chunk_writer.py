from __future__ import annotations

from pathlib import Path


class ChunkWriter:
    """
    Incrementally writes chunks to disk.
    """

    def write(
        self,
        path: str | Path,
        chunks,
    ) -> None:

        file_path = Path(path)

        file_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        with file_path.open("wb") as stream:

            for chunk in chunks:

                stream.write(chunk)