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
from app.services.storage.download_service import DownloadService
from app.services.storage.garbage_collector import GarbageCollector
from app.services.storage.storage_service import StorageService
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
        email="dluser@example.com",
        username="dluser",
        password_hash="hash",
    )
    db_session.add(entity)
    db_session.commit()
    return entity


@pytest.fixture
def keys(db_session):
    return KeyManagementService(
        SQLAlchemyCryptoKeyRepository(db_session)
    )


@pytest.fixture
def key(keys, user):
    return keys.generate_key_pair(
        user.id,
        "primary",
    )


@pytest.fixture
def uploader(db_session, storage, keys):
    return UploadService(
        storage=storage,
        stored_files=SQLAlchemyStoredFileRepository(db_session),
        keys=keys,
    )


@pytest.fixture
def downloader(db_session, storage, keys):
    return DownloadService(
        storage=storage,
        stored_files=SQLAlchemyStoredFileRepository(db_session),
        keys=keys,
    )


@pytest.fixture
def collector(db_session, storage):
    return GarbageCollector(
        storage=storage,
        stored_files=SQLAlchemyStoredFileRepository(db_session),
    )


def test_download_stream_round_trip(
    db_session,
    storage,
    uploader,
    downloader,
    user,
    key,
    tmp_path,
):

    source = tmp_path / "secret.bin"

    payload = b"SecureVault stream " * 1000

    source.write_bytes(payload)

    stored = uploader.upload_file(
        user.id,
        key,
        source,
    )

    import io

    buffer = io.BytesIO()

    sha256, chunk_count = (
        downloader.stream_decrypted(
            stored,
            key,
            buffer,
        )
    )

    assert buffer.getvalue() == payload

    assert sha256 == stored.sha256

    assert chunk_count >= 1


def test_download_to_path(
    db_session,
    storage,
    uploader,
    downloader,
    user,
    key,
    tmp_path,
):

    source = tmp_path / "notes.txt"

    payload = b"restore me\n" * 100

    source.write_bytes(payload)

    stored = uploader.upload_file(
        user.id,
        key,
        source,
    )

    restored = downloader.decrypt_to_path(
        stored,
        key,
        destination=tmp_path / "restored" / "notes.txt",
    )

    assert restored.read_bytes() == payload


def test_restore_folder(
    db_session,
    storage,
    uploader,
    downloader,
    user,
    key,
    tmp_path,
):

    folder = tmp_path / "bundle"

    folder.mkdir()

    (folder / "one.txt").write_text("1")

    (folder / "two.txt").write_text("2")

    stored = uploader.upload_folder(
        user.id,
        key,
        folder,
    )

    restored = downloader.restore_folder(
        stored,
        key,
        destination=tmp_path / "restored",
    )

    assert (restored / "one.txt").read_text() == "1"

    assert (restored / "two.txt").read_text() == "2"


def test_get_for_user_ownership(
    db_session,
    storage,
    uploader,
    downloader,
    user,
    key,
    tmp_path,
):

    import uuid

    source = tmp_path / "owned.txt"

    source.write_text("mine")

    stored = uploader.upload_file(
        user.id,
        key,
        source,
    )

    from app.core.exceptions import NotFoundError

    with pytest.raises(
        NotFoundError
    ):

        downloader.get_for_user(
            uuid.uuid4(),
            stored.id,
        )

    found = downloader.get_for_user(
        user.id,
        stored.id,
    )

    assert found.id == stored.id


def test_restore_folder_rejects_file(
    db_session,
    storage,
    uploader,
    downloader,
    user,
    key,
    tmp_path,
):

    from app.core.exceptions import NotFoundError

    source = tmp_path / "plain.txt"

    source.write_text("data")

    stored = uploader.upload_file(
        user.id,
        key,
        source,
    )

    with pytest.raises(
        NotFoundError
    ):

        downloader.restore_folder(
            stored,
            key,
        )


def test_collect_orphans(
    db_session,
    storage,
    uploader,
    user,
    key,
    collector,
    tmp_path,
):

    source = tmp_path / "keep.txt"

    source.write_text("keep me")

    stored = uploader.upload_file(
        user.id,
        key,
        source,
    )

    stray = storage.container_path(
        user.id,
        __import__("uuid").uuid4(),
    )

    stray.write_bytes(b"SVLT-orphan")

    summary = collector.run_all()

    assert summary["orphaned_containers"] == 1

    assert not stray.exists()

    assert storage.resolve_path(
        stored.storage_path
    ).exists()


def test_collect_missing_records(
    db_session,
    storage,
    uploader,
    user,
    key,
    collector,
    tmp_path,
):

    source = tmp_path / "lost.txt"

    source.write_text("gone")

    stored = uploader.upload_file(
        user.id,
        key,
        source,
    )

    storage.remove_container(stored)

    summary = collector.run_all()

    assert summary["missing_records"] == 1

    from app.infrastructure.repositories.stored_file_repository import (
        SQLAlchemyStoredFileRepository,
    )

    repo = SQLAlchemyStoredFileRepository(db_session)

    refreshed = repo.get(
        stored.id
    )

    assert refreshed.status == "deleted"


def test_purge_deleted(
    db_session,
    storage,
    uploader,
    user,
    key,
    collector,
    tmp_path,
):

    source = tmp_path / "purge.txt"

    source.write_text("purge me")

    stored = uploader.upload_file(
        user.id,
        key,
        source,
    )

    from app.infrastructure.repositories.stored_file_repository import (
        SQLAlchemyStoredFileRepository,
    )

    repo = SQLAlchemyStoredFileRepository(db_session)

    from datetime import UTC, datetime, timedelta

    repo.soft_delete(
        stored,
        datetime.now(UTC) - timedelta(days=400),
    )

    summary = collector.run_all(
        retention_days=365,
    )

    assert summary["purged_deleted"] == 1

    assert not storage.resolve_path(
        stored.storage_path
    ).exists()


def test_cleanup_temp_files(
    db_session,
    storage,
    collector,
):

    old = storage.create_temp_path()

    old.write_bytes(b"stale")

    import os
    import time

    past = time.time() - (48 * 3600)

    os.utime(old, (past, past))

    summary = collector.run_all(
        temp_max_age_hours=24,
    )

    assert summary["temp_files"] == 1

    assert not old.exists()
