import os

import pytest

from app.crypto.exceptions import EncryptionError
from app.crypto.rsa.rsa_service import RSAService
from app.services.encryption.file_decryptor import FileDecryptor
from app.services.encryption.file_encryptor import FileEncryptor
from app.services.encryption.models import EncryptionResult


@pytest.fixture
def keypair():
    return RSAService().generate_key_pair()


@pytest.fixture
def text_file(tmp_path):
    path = tmp_path / "notes.txt"
    path.write_text(
        "SecureVault secret notes\n" * 500,
        encoding="utf-8",
    )
    return path


@pytest.fixture
def binary_file(tmp_path):
    path = tmp_path / "archive.bin"
    path.write_bytes(
        os.urandom(256 * 1024)
    )
    return path


def test_encrypt_text_file(
    tmp_path,
    text_file,
    keypair,
):

    result = FileEncryptor().encrypt_file(
        text_file,
        keypair.public_key,
    )

    assert isinstance(
        result,
        EncryptionResult,
    )

    assert result.success

    assert result.source_path == text_file

    assert result.encrypted_path.exists()

    assert result.file_size == text_file.stat().st_size

    assert result.encrypted_size > result.file_size

    assert len(result.sha256) == 64

    assert result.wrapped_key_size > 0

    assert result.chunk_count >= 1

    assert result.encrypted_path.suffix == ".svlt"

    assert result.compression_ratio > 1


def test_encrypt_binary_file(
    tmp_path,
    binary_file,
    keypair,
):

    result = FileEncryptor().encrypt_file(
        binary_file,
        keypair.public_key,
    )

    assert result.success

    assert result.chunk_count >= 1

    assert result.encrypted_path.exists()

    content = result.encrypted_path.read_bytes()

    assert content[:4] == b"SVLT"


def test_custom_output_path(
    tmp_path,
    text_file,
    keypair,
):

    output = tmp_path / "custom" / "vault.svlt"

    result = FileEncryptor().encrypt_file(
        text_file,
        keypair.public_key,
        output_path=output,
    )

    assert result.encrypted_path == output

    assert output.exists()


def test_custom_chunk_size(
    tmp_path,
    binary_file,
    keypair,
):

    result = FileEncryptor().encrypt_file(
        binary_file,
        keypair.public_key,
        chunk_size=64 * 1024,
    )

    assert result.chunk_count >= 4

    assert result.success


def test_owner_id_in_metadata(
    tmp_path,
    text_file,
    keypair,
):

    result = FileEncryptor().encrypt_file(
        text_file,
        keypair.public_key,
        owner_id="user-1234",
    )

    container = result.encrypted_path.open("rb")

    header = (
        FileDecryptor()
        ._serializer
        .read_header(container)
    )

    container.close()

    assert (
        header["metadata"]["owner_id"]
        == "user-1234"
    )

    assert (
        header["metadata"]["filename"]
        == "notes.txt"
    )


def test_encrypt_missing_file(tmp_path, keypair):

    with pytest.raises(
        EncryptionError
    ):

        FileEncryptor().encrypt_file(
            tmp_path / "missing.txt",
            keypair.public_key,
        )


def test_encrypt_empty_file(
    tmp_path,
    keypair,
):

    empty = tmp_path / "empty.txt"

    empty.write_bytes(b"")

    result = FileEncryptor().encrypt_file(
        empty,
        keypair.public_key,
    )

    assert result.success

    assert result.file_size == 0

    assert result.chunk_count == 0


def test_round_trip_large_file(
    tmp_path,
    keypair,
):

    large = tmp_path / "large.bin"

    large.write_bytes(
        os.urandom(6 * 1024 * 1024)
    )

    encryptor = FileEncryptor()

    result = encryptor.encrypt_file(
        large,
        keypair.public_key,
        chunk_size=1024 * 1024,
    )

    assert result.chunk_count >= 6

    decrypted = FileDecryptor().decrypt_file(
        result.encrypted_path,
        keypair.private_key,
    )

    assert decrypted.decrypted_path.read_bytes() == (
        large.read_bytes()
    )


def test_encrypt_to_stream(
    tmp_path,
    text_file,
    keypair,
):

    import io

    buffer = io.BytesIO()

    result = FileEncryptor().encrypt_to_stream(
        text_file,
        keypair.public_key,
        buffer,
    )

    assert result.success

    assert buffer.getvalue()[:4] == b"SVLT"


def test_metadata_generation(
    tmp_path,
    binary_file,
    keypair,
):

    result = FileEncryptor().encrypt_file(
        binary_file,
        keypair.public_key,
    )

    assert result.sha256

    assert len(result.sha256) == 64
