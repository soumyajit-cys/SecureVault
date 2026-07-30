from app.crypto.models.encrypted_payload import (
    EncryptedPayload,
)
from app.services.encryption.container_serializer import (
    ContainerSerializer,
)


def test_chunk_round_trip(tmp_path):

    serializer = ContainerSerializer()

    file = tmp_path / "chunks.svlt"

    payload = EncryptedPayload(
        nonce="nonce",
        tag="tag",
        ciphertext="cipher",
    )

    with file.open("wb") as fp:

        serializer.write_chunk(
            fp,
            payload,
        )

    with file.open("rb") as fp:

        recovered = serializer.read_chunk(
            fp,
        )

    assert recovered is not None
    assert recovered.nonce == payload.nonce
    assert recovered.tag == payload.tag
    assert recovered.ciphertext == payload.ciphertext