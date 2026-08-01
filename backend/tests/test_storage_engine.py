import uuid

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.domain.models.user import User
from app.infrastructure.database.base import Base
from app.infrastructure.repositories.crypto_key_repository import (
    SQLAlchemyCryptoKeyRepository,
)
from app.infrastructure.repositories.stored_file_repository import (
    SQLAlchemyStoredFileRepository,
)
from app.services.key_management_service import (
    KeyManagementService,
)
from app.services.storage.metadata_service import MetadataService
from app.services.storage.storage_service import (
    StoragePathError,
    StorageService,
)
from app.services.storage.upload_service import UploadService


@pytest.fixture
def db_session(tmp_path):

    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )

    Base.metadata.create_all(engine)

    TestingSessionLocal = sessionmaker(
        bind=engine,
        autoflush=False,
        expire_on_commit=False,
    )

    session = TestingSessionLocal()

    yield session

    session.close()

    engine.dispose()


@pytest.fixture
def storage(tmp_path):
    return StorageService(
        storage_dir=tmp_path / "storage"
    )


@pytest.fixture
def user(db_session):
    entity = User(
        email="storuser@example.com",
        username="storuser",
        password_hash="hash",
    )
    db_session.add(entity)
    db_session.commit()
    return entity


@pytest.fixture
def uploader(db_session, storage):
    return UploadService(
        storage=storage,
        stored_files=SQLAlchemyStoredFileRepository(db_session),
        keys=KeyManagementService(
            SQLAlchemyCryptoKeyRepository(db_session)
        ),
    )


@pytest.fixture
def metadb(db_session, storage):
    return MetadataService(
        storage=storage,
        stored_files=SQLAlchemyStoredFileRepository(db_session),
    )


@pytest.fixture
def key(db_session, user):
    service = KeyManagementService(
        SQLAlchemyCryptoKeyRepository(db_session)
    )
    return service.generate_key_pair(
        user.id,
        "primary",
    )


def test_storage_layout_created(storage):

    assert storage.files_dir.is_dir()

    assert storage.temp_dir.is_dir()

    assert storage.vault_dir.is_dir()


def test_container_path_is_under_user_dir(storage):

    user_id = uuid.uuid4()

    file_id = uuid.uuid4()

    path = storage.container_path(
        user_id,
        file_id,
    )

    assert str(path).startswith(
        str(storage.files_dir / str(user_id))
    )

    assert path.name == f"{file_id}.svlt"


def test_relative_and_resolve_round_trip(storage):

    path = storage.container_path(
        uuid.uuid4(),
        uuid.uuid4(),
    )

    relative = storage.relative_path(path)

    resolved = storage.resolve_path(relative)

    assert resolved == path


def test_resolve_rejects_traversal(storage):

    with pytest.raises(
        StoragePathError
    ):

        storage.resolve_path(
            "../../etc/passwd"
        )


def test_temp_path_unique(storage):

    first = storage.create_temp_path()

    second = storage.create_temp_path()

    assert first != second

    assert first.parent == storage.temp_dir


def test_remove_file(storage):

    temp = storage.create_temp_path()

    temp.write_bytes(b"data")

    assert storage.remove(temp) is True

    assert not temp.exists()


def test_remove_missing(storage):

    assert storage.remove(
        storage.temp_dir / "nope"
    ) is False


def test_remove_temp_files_older_than(storage):

    old = storage.create_temp_path()

    old.write_bytes(b"stale")

    import os
    import time

    past = time.time() - (48 * 3600)

    os.utime(old, (past, past))

    fresh = storage.create_temp_path()

    fresh.write_bytes(b"fresh")

    removed = storage.remove_temp_files_older_than(
        24
    )

    assert removed == 1

    assert not old.exists()

    assert fresh.exists()


def test_upload_file_and_metadata(
    db_session,
    storage,
    uploader,
    metadb,
    user,
    key,
    tmp_path,
):

    source = tmp_path / "doc.txt"

    source.write_text(
        "Top secret document\n" * 100,
        encoding="utf-8",
    )

    stored = uploader.upload_file(
        user.id,
        key,
        source,
    )

    assert stored.id is not None

    assert stored.user_id == user.id

    assert stored.key_id == key.id

    assert stored.original_filename == "doc.txt"

    assert stored.original_size == source.stat().st_size

    assert stored.encrypted_size > 0

    assert len(stored.sha256) == 64

    assert stored.status == "active"

    assert stored.is_folder is False

    container = storage.resolve_path(
        stored.storage_path
    )

    assert container.is_file()

    assert container.read_bytes()[:4] == b"SVLT"

    fetched = metadb.get(
        user.id,
        stored.id,
    )

    assert fetched.id == stored.id


def test_upload_stream_source(
    db_session,
    storage,
    uploader,
    user,
    key,
):

    import io

    stream = io.BytesIO(
        b"streamed content " * 500
    )

    stored = uploader.upload_file(
        user.id,
        key,
        stream,
        filename="stream.bin",
    )

    assert stored.original_filename == "stream.bin"

    assert stored.encrypted_size > 0


def test_upload_missing_file(
    db_session,
    storage,
    uploader,
    user,
    key,
    tmp_path,
):

    from app.core.exceptions import NotFoundError

    with pytest.raises(
        NotFoundError
    ):

        uploader.upload_file(
            user.id,
            key,
            tmp_path / "missing.txt",
        )


def test_upload_folder(
    db_session,
    storage,
    uploader,
    metadb,
    user,
    key,
    tmp_path,
):

    folder = tmp_path / "docs"

    folder.mkdir()

    (folder / "a.txt").write_text("aaa")

    (folder / "b.txt").write_text("bbb")

    stored = uploader.upload_folder(
        user.id,
        key,
        folder,
    )

    assert stored.is_folder is True

    assert stored.folder_file_count == 2

    assert stored.mime_type == (
        "application/x-svlt-folder"
    )

    listing, total = metadb.list(
        user.id,
        is_folder=True,
    )

    assert total == 1


def test_register_container(
    db_session,
    storage,
    uploader,
    user,
    key,
    tmp_path,
):

    container = tmp_path / "premade.svlt"

    container.write_bytes(
        b"SVLT-encrypted-bytes"
    )

    stored = uploader.register_container(
        user.id,
        key,
        container,
        filename="premade.svlt",
    )

    assert stored.encrypted_size == len(
        b"SVLT-encrypted-bytes"
    )

    assert stored.original_filename == "premade.svlt"


def test_list_pagination_filtering(
    db_session,
    storage,
    uploader,
    metadb,
    user,
    key,
    tmp_path,
):

    for i in range(5):

        source = tmp_path / f"file_{i}.txt"

        source.write_text(
            f"content {i}",
            encoding="utf-8",
        )

        uploader.upload_file(
            user.id,
            key,
            source,
        )

    items, total = metadb.list(
        user.id,
        page=1,
        page_size=2,
    )

    assert total == 5

    assert len(items) == 2

    items, total = metadb.list(
        user.id,
        page=3,
        page_size=2,
    )

    assert len(items) == 1

    items, total = metadb.list(
        user.id,
        search="file_3",
    )

    assert total == 1

    assert items[0].original_filename == "file_3.txt"


def test_soft_delete_and_purge(
    db_session,
    storage,
    uploader,
    metadb,
    user,
    key,
    tmp_path,
):

    source = tmp_path / "del.txt"

    source.write_text("to delete")

    stored = uploader.upload_file(
        user.id,
        key,
        source,
    )

    deleted = metadb.soft_delete(
        user.id,
        stored.id,
    )

    assert deleted.status == "deleted"

    assert deleted.deleted_at is not None

    container = storage.resolve_path(
        stored.storage_path
    )

    assert container.exists()

    purged = metadb.purge(
        user.id,
        stored.id,
    )

    assert purged is True

    assert not container.exists()


def test_storage_summary(
    db_session,
    storage,
    uploader,
    metadb,
    user,
    key,
    tmp_path,
):

    source = tmp_path / "sum.txt"

    source.write_bytes(b"x" * 1000)

    uploader.upload_file(
        user.id,
        key,
        source,
    )

    summary = metadb.storage_summary(
        user.id
    )

    assert summary["file_count"] == 1

    assert summary["encrypted_bytes"] > 0


def test_rename(
    db_session,
    storage,
    uploader,
    metadb,
    user,
    key,
    tmp_path,
):

    source = tmp_path / "old.txt"

    source.write_text("data")

    stored = uploader.upload_file(
        user.id,
        key,
        source,
    )

    renamed = metadb.rename(
        user.id,
        stored.id,
        "new.txt",
    )

    assert renamed.original_filename == "new.txt"
