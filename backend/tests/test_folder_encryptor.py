import os

import pytest

from app.crypto.exceptions import EncryptionError
from app.crypto.rsa.rsa_service import RSAService
from app.services.encryption.folder_decryptor import FolderDecryptor
from app.services.encryption.folder_encryptor import (
    FolderEncryptionResult,
    FolderEncryptor,
)


@pytest.fixture
def keypair():
    return RSAService().generate_key_pair()


@pytest.fixture
def folder_tree(tmp_path):
    root = tmp_path / "documents"
    root.mkdir()

    (root / "reports").mkdir()
    (root / "reports" / "2026").mkdir()

    (root / "notes.txt").write_text(
        "Meeting notes\n" * 200,
        encoding="utf-8",
    )

    (root / "reports" / "2026" / "q1.pdf").write_bytes(
        os.urandom(128 * 1024)
    )

    (root / "reports" / "2026" / "q2.pdf").write_bytes(
        os.urandom(64 * 1024)
    )

    return root


def test_encrypt_folder(
    tmp_path,
    folder_tree,
    keypair,
):

    result = FolderEncryptor().encrypt_folder(
        folder_tree,
        keypair.public_key,
    )

    assert isinstance(
        result,
        FolderEncryptionResult,
    )

    assert result.success

    assert result.file_count == 3

    assert result.directory_count == 2

    assert result.encrypted_path.exists()

    assert result.archive_path.exists()

    assert result.encrypted_size > 0

    assert result.encryption.success


def test_encrypt_folder_custom_output(
    tmp_path,
    folder_tree,
    keypair,
):

    output = tmp_path / "vault" / "docs.svlt"

    result = FolderEncryptor().encrypt_folder(
        folder_tree,
        keypair.public_key,
        output_path=output,
    )

    assert result.encrypted_path == output

    assert output.exists()


def test_folder_round_trip(
    tmp_path,
    folder_tree,
    keypair,
):

    result = FolderEncryptor().encrypt_folder(
        folder_tree,
        keypair.public_key,
    )

    restored = FolderDecryptor().decrypt_folder(
        result.encrypted_path,
        keypair.private_key,
        destination=tmp_path / "restored",
    )

    assert restored.success

    assert restored.restored_files == 3

    assert restored.restored_directories == 2

    assert (
        restored.restored_folder / "notes.txt"
    ).read_text(encoding="utf-8") == (
        "Meeting notes\n" * 200
    )

    assert (
        restored.restored_folder
        / "reports"
        / "2026"
        / "q1.pdf"
    ).read_bytes() == (
        folder_tree / "reports" / "2026" / "q1.pdf"
    ).read_bytes()


def test_folder_round_trip_default_destination(
    tmp_path,
    folder_tree,
    keypair,
):

    result = FolderEncryptor().encrypt_folder(
        folder_tree,
        keypair.public_key,
    )

    restored = FolderDecryptor().decrypt_folder(
        result.encrypted_path,
        keypair.private_key,
    )

    assert restored.success

    assert restored.restored_folder.is_dir()


def test_encrypt_missing_folder(tmp_path, keypair):

    with pytest.raises(
        EncryptionError
    ):

        FolderEncryptor().encrypt_folder(
            tmp_path / "missing",
            keypair.public_key,
        )


def test_decrypt_missing_container(tmp_path, keypair):

    with pytest.raises(
        EncryptionError
    ):

        FolderDecryptor().decrypt_folder(
            tmp_path / "missing.svlt",
            keypair.private_key,
        )


def test_decrypt_folder_wrong_key(
    tmp_path,
    folder_tree,
    keypair,
):

    result = FolderEncryptor().encrypt_folder(
        folder_tree,
        keypair.public_key,
    )

    other = RSAService().generate_key_pair()

    import pytest as pt

    with pt.raises(
        Exception
    ):

        FolderDecryptor().decrypt_folder(
            result.encrypted_path,
            other.private_key,
        )


def test_large_folder_support(
    tmp_path,
    keypair,
):

    root = tmp_path / "big"

    root.mkdir()

    for i in range(30):

        (root / f"file_{i}.bin").write_bytes(
            os.urandom(256 * 1024)
        )

    result = FolderEncryptor().encrypt_folder(
        root,
        keypair.public_key,
    )

    assert result.file_count == 30

    restored = FolderDecryptor().decrypt_folder(
        result.encrypted_path,
        keypair.private_key,
        destination=tmp_path / "big_restored",
    )

    assert restored.restored_files == 30
