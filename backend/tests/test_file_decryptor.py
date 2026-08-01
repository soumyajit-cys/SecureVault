import os

import pytest

from app.crypto.exceptions import (
    DecryptionError,
    IntegrityVerificationError,
    InvalidKeyError,
)

from app.crypto.rsa.rsa_service import RSAService
from app.services.encryption.file_decryptor import FileDecryptor
from app.services.encryption.file_encryptor import FileEncryptor
from app.services.encryption.models import DecryptionResult


@pytest.fixture
def keypair():
    return RSAService().generate_key_pair()


@pytest.fixture
def encrypted_text(tmp_path, keypair):
    source = tmp_path / "report.txt"
    source.write_text(
        "Confidential report " * 2000,
        encoding="utf-8",
    )
    return FileEncryptor().encrypt_file(
        source,
        keypair.public_key,
    )


def test_decrypt_round_trip(
    tmp_path,
    encrypted_text,
    keypair,
):

    original = (
        encrypted_text.source_path.read_bytes()
    )

    result = FileDecryptor().decrypt_file(
        encrypted_text.encrypted_path,
        keypair.private_key,
    )

    assert isinstance(
        result,
        DecryptionResult,
    )

    assert result.success

    assert result.integrity_verified

    assert result.decrypted_path.read_bytes() == original

    assert result.decrypted_size == len(original)

    assert len(result.sha256) == 64

    assert result.sha256 == encrypted_text.sha256

    assert result.chunk_count >= 1

    assert result.file_size > result.decrypted_size


def test_decrypt_restores_original_filename(
    tmp_path,
    encrypted_text,
    keypair,
):

    result = FileDecryptor().decrypt_file(
        encrypted_text.encrypted_path,
        keypair.private_key,
    )

    assert result.decrypted_path.name == "report.txt"


def test_decrypt_custom_output(
    tmp_path,
    encrypted_text,
    keypair,
):

    output = tmp_path / "restored" / "custom.txt"

    result = FileDecryptor().decrypt_file(
        encrypted_text.encrypted_path,
        keypair.private_key,
        output_path=output,
    )

    assert result.decrypted_path == output

    assert output.exists()


def test_decrypt_with_wrong_key(
    tmp_path,
    encrypted_text,
    keypair,
):

    other_keypair = (
        RSAService().generate_key_pair()
    )

    with pytest.raises(
        DecryptionError
    ):

        FileDecryptor().decrypt_file(
            encrypted_text.encrypted_path,
            other_keypair.private_key,
        )


def test_decrypt_corrupted_container(tmp_path, keypair):

    source = tmp_path / "data.txt"

    source.write_text(
        "SecureVault payload",
        encoding="utf-8",
    )

    result = FileEncryptor().encrypt_file(
        source,
        keypair.public_key,
    )

    data = bytearray(
        result.encrypted_path.read_bytes()
    )

    data[-20] ^= 0xFF

    corrupted = tmp_path / "corrupted.svlt"

    corrupted.write_bytes(bytes(data))

    with pytest.raises(
        DecryptionError
    ):

        FileDecryptor().decrypt_file(
            corrupted,
            keypair.private_key,
        )


def test_decrypt_tampered_plaintext_detected(
    tmp_path,
    keypair,
):

    source = tmp_path / "payload.bin"

    source.write_bytes(
        os.urandom(128 * 1024)
    )

    encrypted = FileEncryptor().encrypt_file(
        source,
        keypair.public_key,
    )

    container = bytearray(
        encrypted.encrypted_path.read_bytes()
    )

    header_len = int.from_bytes(
        container[8:12],
        "big",
    )

    meta_offset = 12 + header_len

    key_len = int.from_bytes(
        container[meta_offset: meta_offset + 4],
        "big",
    )

    first_nonce_offset = meta_offset + 4 + key_len + 4

    container[first_nonce_offset + 2] ^= 0xFF

    tampered = tmp_path / "tampered.svlt"

    tampered.write_bytes(bytes(container))

    with pytest.raises(
        DecryptionError
    ):

        FileDecryptor().decrypt_file(
            tampered,
            keypair.private_key,
        )


def test_decrypt_invalid_container(tmp_path, keypair):

    invalid = tmp_path / "not-a-container.svlt"

    invalid.write_bytes(
        b"this is not a securevault container"
    )

    with pytest.raises(
        DecryptionError
    ):

        FileDecryptor().decrypt_file(
            invalid,
            keypair.private_key,
        )


def test_decrypt_missing_file(tmp_path, keypair):

    with pytest.raises(
        DecryptionError
    ):

        FileDecryptor().decrypt_file(
            tmp_path / "missing.svlt",
            keypair.private_key,
        )


def test_decrypt_invalid_private_key(tmp_path):

    with pytest.raises(
        InvalidKeyError
    ):

        RSAService().load_private_key(
            b"-----BEGIN PRIVATE KEY-----\n"
            b"NOT A KEY\n"
            b"-----END PRIVATE KEY-----"
        )


def test_integrity_check_off(
    tmp_path,
    keypair,
):

    source = tmp_path / "doc.txt"

    source.write_text(
        "Integrity check bypass",
        encoding="utf-8",
    )

    encrypted = FileEncryptor().encrypt_file(
        source,
        keypair.public_key,
    )

    result = FileDecryptor().decrypt_file(
        encrypted.encrypted_path,
        keypair.private_key,
        verify_integrity=False,
    )

    assert result.success

    assert result.sha256 == encrypted.sha256


def test_decrypt_to_stream(
    tmp_path,
    encrypted_text,
    keypair,
):

    import io

    buffer = io.BytesIO()

    sha256, chunk_count = (
        FileDecryptor().decrypt_to_stream(
            encrypted_text.encrypted_path,
            keypair.private_key,
            buffer,
        )
    )

    assert buffer.getvalue() == (
        encrypted_text.source_path.read_bytes()
    )

    assert sha256 == encrypted_text.sha256

    assert chunk_count >= 1


def test_decrypt_verify_against_stored_digest(
    tmp_path,
    encrypted_text,
    keypair,
):

    result = FileDecryptor().decrypt_file(
        encrypted_text.encrypted_path,
        keypair.private_key,
    )

    assert result.integrity_verified is True

    assert result.sha256 == encrypted_text.sha256
