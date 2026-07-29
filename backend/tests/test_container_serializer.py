from pathlib import Path

from app.crypto.file.file_header import FileHeader
from app.services.encryption.container_serializer import (
    ContainerSerializer,
)


def test_container_round_trip(tmp_path: Path):

    serializer = ContainerSerializer()

    header = FileHeader()

    wrapped_key = b"securevault-test-key"

    file_path = tmp_path / "sample.svlt"

    stream = serializer.write_file(
        file_path,
        header,
        wrapped_key,
    )

    stream.close()

    stream, loaded_header, loaded_key = (
        serializer.open_file(file_path)
    )

    stream.close()

    assert loaded_header["version"] == 1

    assert loaded_header["algorithm"] == "AES-256-GCM"

    assert loaded_key == wrapped_key