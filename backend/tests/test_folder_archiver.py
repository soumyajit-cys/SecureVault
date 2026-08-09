import os

import pytest

from app.services.encryption.folder_archiver import (
    ArchiveError,
    FolderArchiver,
)


@pytest.fixture
def folder_tree(tmp_path):
    root = tmp_path / "project"
    root.mkdir()

    (root / "src").mkdir()
    (root / "src" / "nested").mkdir()
    (root / "empty_dir").mkdir()

    (root / "README.md").write_text(
        "# SecureVault project\n",
        encoding="utf-8",
    )

    (root / "src" / "main.py").write_text(
        "print('hello')\n",
        encoding="utf-8",
    )

    (root / "src" / "nested" / "data.bin").write_bytes(
        os.urandom(64 * 1024)
    )

    return root


def test_create_archive(folder_tree, tmp_path):

    archive = FolderArchiver().create_archive(
        folder_tree,
        tmp_path / "out" / "project.zip",
    )

    assert archive.exists()

    assert archive.stat().st_size > 0


def test_create_archive_default_path(folder_tree):

    archive = FolderArchiver().create_archive(
        folder_tree,
    )

    assert archive == folder_tree.with_suffix(".zip")

    assert archive.exists()


def test_round_trip_restores_structure(
    folder_tree,
    tmp_path,
):

    archive = FolderArchiver().create_archive(
        folder_tree,
        tmp_path / "project.zip",
    )

    dest = tmp_path / "restored"

    FolderArchiver().extract_archive(
        archive,
        dest,
    )

    assert (
        dest / "README.md"
    ).read_text(encoding="utf-8") == (
        "# SecureVault project\n"
    )

    assert (
        dest / "src" / "nested" / "data.bin"
    ).read_bytes() == (
        folder_tree / "src" / "nested" / "data.bin"
    ).read_bytes()

    assert (dest / "empty_dir").is_dir()


def test_recursive_traversal_counts(
    folder_tree,
    tmp_path,
):

    archive = FolderArchiver().create_archive(
        folder_tree,
        tmp_path / "project.zip",
    )

    import zipfile

    with zipfile.ZipFile(archive) as zf:

        names = set(
            zf.namelist()
        )

    assert "src/main.py" in names

    assert "src/nested/data.bin" in names

    assert "empty_dir/" in names


def test_missing_folder(tmp_path):

    with pytest.raises(
        ArchiveError
    ):

        FolderArchiver().create_archive(
            tmp_path / "missing"
        )


def test_missing_archive(tmp_path):

    with pytest.raises(
        ArchiveError
    ):

        FolderArchiver().extract_archive(
            tmp_path / "missing.zip",
            tmp_path / "dest",
        )


def test_invalid_archive(tmp_path):

    bad = tmp_path / "bad.zip"

    bad.write_bytes(b"not a zip file")

    with pytest.raises(
        ArchiveError
    ):

        FolderArchiver().extract_archive(
            bad,
            tmp_path / "dest",
        )


def test_extract_rejects_path_traversal(tmp_path):

    import zipfile

    evil = tmp_path / "evil.zip"

    with zipfile.ZipFile(evil, "w") as zf:

        zf.writestr(
            "../escaped.txt",
            "pwned",
        )

    with pytest.raises(
        ArchiveError
    ):

        FolderArchiver().extract_archive(
            evil,
            tmp_path / "dest",
        )


def test_extract_rejects_duplicate_entries(tmp_path):

    import zipfile

    dup = tmp_path / "dup.zip"

    with zipfile.ZipFile(dup, "w") as zf:

        zf.writestr("a.txt", "first")

        zf.writestr("a.txt", "second")

    with pytest.raises(
        ArchiveError
    ):

        FolderArchiver().extract_archive(
            dup,
            tmp_path / "dest",
        )


def test_extract_rejects_absolute_path(tmp_path):

    import zipfile

    absolute = tmp_path / "abs.zip"

    with zipfile.ZipFile(absolute, "w") as zf:

        zf.writestr("/etc/passwd", "pwned")

    with pytest.raises(
        ArchiveError
    ):

        FolderArchiver().extract_archive(
            absolute,
            tmp_path / "dest",
        )


def test_symlinks_skipped(
    tmp_path,
):

    root = tmp_path / "symlink_dir"

    root.mkdir()

    (root / "real.txt").write_text("data")

    try:

        os.symlink(
            "/nonexistent-target",
            root / "link.txt",
        )

    except OSError:
        pytest.skip(
            "symlinks unavailable on this platform"
        )

    archive = FolderArchiver().create_archive(
        root,
        tmp_path / "symlink_dir.zip",
    )

    import zipfile

    with zipfile.ZipFile(archive) as zf:

        names = set(
            zf.namelist()
        )

    assert "link.txt" not in names

    assert "real.txt" in names


def test_extract_rejects_zip_bomb(tmp_path):
    """
    A tiny archive declaring an enormous uncompressed
    member must be rejected before any data is written.
    """

    import struct
    import time
    import zlib

    declared_size = 3 * 1024 * 1024 * 1024

    payload = b"x" * 1024

    compressed = zlib.compress(payload)

    crc = zlib.crc32(payload) & 0xFFFFFFFF

    now = time.localtime()

    dostime = (
        (now.tm_hour << 11)
        | (now.tm_min << 5)
        | (now.tm_sec // 2)
    )

    dostdate = (
        ((now.tm_year - 1980) << 9)
        | (now.tm_mon << 5)
        | now.tm_mday
    )

    name = b"bomb.bin"

    local = struct.pack(
        "<IHHHHHIIIHH",
        0x04034B50,
        20,
        0,
        8,
        dostime,
        dostdate,
        crc,
        len(compressed),
        declared_size,
        len(name),
        0,
    )

    central = struct.pack(
        "<IHHHHHHIIIHHHHHII",
        0x02014B50,
        20,
        20,
        0,
        8,
        dostime,
        dostdate,
        crc,
        len(compressed),
        declared_size,
        len(name),
        0,
        0,
        0,
        0,
        0,
        0,
    )

    central_offset = (
        len(local) + len(name) + len(compressed)
    )

    eocd = struct.pack(
        "<IHHHHIIH",
        0x06054B50,
        0,
        0,
        1,
        1,
        central_offset + len(central) + len(name),
        30,
    )

    archive_path = tmp_path / "bomb.zip"

    archive_path.write_bytes(
        local
        + name
        + compressed
        + central
        + name
        + eocd
    )

    destination = tmp_path / "out"

    with pytest.raises(
        ArchiveError,
        match="compression limit",
    ):

        FolderArchiver().extract_archive(
            archive_path,
            destination,
        )

    assert not (destination / "bomb.bin").exists()


def test_extract_respects_total_size_cap(tmp_path):
    """
    The cumulative extracted size must never exceed the
    configured cap, even when each member passes the
    per-member ratio guard.
    """

    import io
    import zipfile

    buffer = io.BytesIO()

    with zipfile.ZipFile(
        buffer,
        "w",
        zipfile.ZIP_DEFLATED,
    ) as archive:

        archive.writestr(
            "one.bin",
            b"a" * (2 * 1024 * 1024),
        )

        archive.writestr(
            "two.bin",
            b"b" * (2 * 1024 * 1024),
        )

    archive_path = tmp_path / "cap.zip"

    archive_path.write_bytes(
        buffer.getvalue()
    )

    destination = tmp_path / "out"

    with pytest.raises(
        ArchiveError,
        match="extraction limit",
    ):

        FolderArchiver().extract_archive(
            archive_path,
            destination,
            max_total_size=3 * 1024 * 1024,
        )

    assert not (destination / "two.bin").exists()
