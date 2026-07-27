from pathlib import Path

from app.crypto.streams import ChunkReader


def test_chunk_reader(tmp_path):

    file = tmp_path / "data.bin"

    file.write_bytes(
        b"A" * (1024 * 1024)
    )

    reader = ChunkReader(
        chunk_size=65536
    )

    chunks = list(
        reader.read(file)
    )

    assert len(chunks) > 1

    assert b"".join(chunks) == file.read_bytes()