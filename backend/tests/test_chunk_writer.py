from pathlib import Path

from app.crypto.streams import ChunkWriter


def test_chunk_writer(tmp_path):

    output = tmp_path / "output.bin"

    chunks = [
        b"abc",
        b"def",
        b"ghi",
    ]

    ChunkWriter().write(
        output,
        chunks,
    )

    assert output.read_bytes() == b"abcdefghi"