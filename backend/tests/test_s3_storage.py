import hashlib
import io
import uuid
from unittest import mock

import boto3
import pytest
from moto import mock_aws
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.exceptions import NotFoundError
from app.core.security_settings import validate_storage_settings
from app.domain.models.user import User
from app.infrastructure.database.base import Base
from app.infrastructure.repositories.crypto_key_repository import (
    SQLAlchemyCryptoKeyRepository,
)
from app.infrastructure.repositories.file_share_repository import (
    SQLAlchemyFileShareRepository,
)
from app.infrastructure.repositories.stored_file_repository import (
    SQLAlchemyStoredFileRepository,
)
from app.infrastructure.repositories.user_repository import (
    SQLAlchemyUserRepository,
)
from app.infrastructure.storage.factory import build_object_store
from app.infrastructure.storage.local_store import LocalObjectStore
from app.infrastructure.storage.s3_store import S3ObjectStore
from app.services.file_share_service import ShareService
from app.services.key_management_service import KeyManagementService
from app.services.storage.download_service import DownloadService
from app.services.storage.garbage_collector import GarbageCollector
from app.services.storage.storage_service import StorageService
from app.services.storage.upload_service import UploadService

BUCKET = "securevault-test"
REGION = "us-east-1"
# NOTE: moto only intercepts AWS endpoints, so tests use one.
# Backblaze B2 compatibility comes from boto3's standard
# ``endpoint_url`` mechanism — the exact same code path, with
# the endpoint string and region passed through verbatim
# (production B2 form: https://s3.<region>.backblazeb2.com).
ENDPOINT = "https://s3.us-east-1.amazonaws.com"


@pytest.fixture
def aws_env(monkeypatch):
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")
    monkeypatch.setenv("AWS_SECURITY_TOKEN", "testing")
    monkeypatch.setenv("AWS_SESSION_TOKEN", "testing")
    monkeypatch.setenv("AWS_DEFAULT_REGION", REGION)


@pytest.fixture
def s3_bucket(aws_env):
    with mock_aws():
        client = boto3.client("s3", region_name=REGION)
        client.create_bucket(Bucket=BUCKET)
        yield client


@pytest.fixture
def s3_store(s3_bucket):
    # NOTE: the mock is active for the whole test via the
    # s3_bucket fixture; the store builds its own boto3 client
    # lazily on first use, which moto intercepts.
    return S3ObjectStore(
        endpoint_url=ENDPOINT,
        bucket=BUCKET,
        access_key="testing",
        secret_key="testing",
        region=REGION,
    )


@pytest.fixture
def db_session():
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
def storage(tmp_path, s3_store):
    return StorageService(
        storage_dir=tmp_path / "storage",
        backend="s3",
        object_store=s3_store,
    )


@pytest.fixture
def user(db_session):
    entity = User(
        email="s3user@example.com",
        username="s3user",
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
    return keys.generate_key_pair(user.id, "primary")


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


# -------------------------------------------------
# ObjectStore contract (S3)
# -------------------------------------------------


def test_s3_round_trip(s3_store):
    key = "files/u/f.svlt"
    payload = b"hello s3 " * 100

    written = s3_store.put(key, io.BytesIO(payload))

    assert written == len(payload)
    assert s3_store.exists(key)
    assert s3_store.size(key) == len(payload)

    with s3_store.open(key) as stream:
        assert stream.read() == payload

    assert list(s3_store.iter_keys("files/")) == [key]

    assert s3_store.delete(key) is True
    assert s3_store.delete(key) is False
    assert not s3_store.exists(key)
    assert s3_store.size(key) is None

    with pytest.raises(NotFoundError):
        s3_store.open(key)


def test_s3_rejects_unsafe_keys(s3_store):
    with pytest.raises(ValueError):
        s3_store.put("/abs.svlt", io.BytesIO(b"x"))

    with pytest.raises(ValueError):
        s3_store.put("files/../evil.svlt", io.BytesIO(b"x"))


def test_s3_write_abort_leaves_no_object(s3_store):
    with pytest.raises(RuntimeError):
        with s3_store.write("files/u/aborted.svlt"):
            raise RuntimeError("boom")

    assert not s3_store.exists("files/u/aborted.svlt")


def test_s3_zero_byte_object(s3_store):
    s3_store.put("files/u/empty.svlt", io.BytesIO(b""))

    assert s3_store.exists("files/u/empty.svlt")
    assert s3_store.size("files/u/empty.svlt") == 0

    with s3_store.open("files/u/empty.svlt") as stream:
        assert stream.read() == b""


def test_s3_multipart_streams_large_objects(s3_bucket):
    """11 MiB through 5 MiB parts must upload as 3 parts with a
    bounded writer buffer — never the whole object in memory."""

    store = S3ObjectStore(
        endpoint_url=ENDPOINT,
        bucket=BUCKET,
        access_key="testing",
        secret_key="testing",
        region=REGION,
        part_size=5 * 1024 * 1024,
    )

    payload = bytes((i % 251 for i in range(11 * 1024 * 1024)))

    client = store._get_client()
    real_upload_part = client.upload_part
    calls = []

    def counting_upload_part(**kwargs):
        calls.append(kwargs["PartNumber"])
        return real_upload_part(**kwargs)

    with mock.patch.object(
        client, "upload_part", side_effect=counting_upload_part
    ):
        with store.write("files/u/big.svlt") as out:
            for offset in range(0, len(payload), 1024 * 1024):
                out.write(payload[offset : offset + 1024 * 1024])
            # Writer buffer must stay bounded by one part.
            assert len(out._buffer) < store.part_size

    assert sorted(calls) == [1, 2, 3]
    assert store.size("files/u/big.svlt") == len(payload)

    digest = hashlib.sha256()
    with store.open("files/u/big.svlt") as stream:
        while True:
            chunk = stream.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)

    assert digest.digest() == hashlib.sha256(payload).digest()


# -------------------------------------------------
# End-to-end over S3 (crypto untouched)
# -------------------------------------------------


def test_s3_upload_download_round_trip(
    storage, uploader, downloader, user, key, tmp_path
):
    source = tmp_path / "secret.bin"
    payload = b"SecureVault over S3 " * 5000
    source.write_bytes(payload)

    stored = uploader.upload_file(user.id, key, source)

    assert stored.storage_path == (
        f"files/{user.id}/{stored.id}.svlt"
    )
    # Committed bytes live in the bucket, not on disk.
    assert storage.container_exists(stored.storage_path)

    buffer = io.BytesIO()
    sha256, chunk_count = downloader.stream_decrypted(
        stored, key, buffer
    )

    assert buffer.getvalue() == payload
    assert sha256 == stored.sha256 == hashlib.sha256(payload).hexdigest()
    assert chunk_count >= 1


def test_s3_stream_upload_source(
    uploader, downloader, user, key, tmp_path
):
    payload = b"streaming upload " * 1000

    stored = uploader.upload_file(
        user.id,
        key,
        io.BytesIO(payload),
        filename="stream.bin",
    )

    buffer = io.BytesIO()
    downloader.stream_decrypted(stored, key, buffer)

    assert buffer.getvalue() == payload


def test_s3_decrypt_to_path(
    uploader, downloader, user, key, tmp_path
):
    source = tmp_path / "notes.txt"
    payload = b"restore me\n" * 100
    source.write_bytes(payload)

    stored = uploader.upload_file(user.id, key, source)

    restored = downloader.decrypt_to_path(
        stored, key, destination=tmp_path / "restored" / "notes.txt"
    )

    assert restored.read_bytes() == payload


def test_s3_folder_round_trip(
    uploader, downloader, user, key, tmp_path
):
    folder = tmp_path / "bundle"
    folder.mkdir()
    (folder / "one.txt").write_text("1")
    (folder / "two.txt").write_text("2")

    stored = uploader.upload_folder(user.id, key, folder)

    assert stored.is_folder
    assert stored.folder_file_count == 2

    restored = downloader.restore_folder(
        stored, key, destination=tmp_path / "restored"
    )

    assert (restored / "one.txt").read_text() == "1"
    assert (restored / "two.txt").read_text() == "2"


def test_s3_register_container(
    uploader, downloader, user, key, tmp_path
):
    from app.services.encryption.file_encryptor import FileEncryptor
    from app.crypto.rsa.rsa_service import RSAService

    raw = tmp_path / "pre.bin"
    raw.write_bytes(b"pre-encrypted registration")

    public = RSAService().load_public_key(
        key.public_key_pem.encode()
    )
    staged = tmp_path / "pre.bin.svlt"
    FileEncryptor().encrypt_file(raw, public, output_path=staged)

    stored = uploader.register_container(
        user.id, key, staged, filename="pre.bin"
    )

    buffer = io.BytesIO()
    downloader.stream_decrypted(stored, key, buffer)

    assert buffer.getvalue() == b"pre-encrypted registration"


def test_s3_share_reads_wrapped_key(
    db_session, storage, uploader, user, key, tmp_path
):
    source = tmp_path / "shared.txt"
    source.write_bytes(b"share me")

    stored = uploader.upload_file(user.id, key, source)

    shares = ShareService(
        SQLAlchemyFileShareRepository(db_session),
        SQLAlchemyStoredFileRepository(db_session),
        SQLAlchemyUserRepository(db_session),
        KeyManagementService(
            SQLAlchemyCryptoKeyRepository(db_session)
        ),
        storage=storage,
    )

    wrapped = shares._read_owner_wrapped_key(stored)

    assert isinstance(wrapped, bytes) and len(wrapped) > 0


def test_s3_garbage_collection(
    db_session, storage, uploader, user, key, collector, tmp_path
):
    from app.infrastructure.repositories.stored_file_repository import (
        SQLAlchemyStoredFileRepository,
    )

    source = tmp_path / "keep.txt"
    source.write_text("keep me")
    stored = uploader.upload_file(user.id, key, source)

    stray_key = f"files/{user.id}/{uuid.uuid4()}.svlt"
    storage.put_container(stray_key, io.BytesIO(b"SVLT-orphan"))

    summary = collector.run_all()

    assert summary["orphaned_containers"] == 1
    assert not storage.container_exists(stray_key)
    assert storage.container_exists(stored.storage_path)

    storage.delete_container(stored.storage_path)
    summary = collector.run_all()

    assert summary["missing_records"] == 1

    repo = SQLAlchemyStoredFileRepository(db_session)
    assert repo.get(stored.id).status == "deleted"


# -------------------------------------------------
# Factory + startup validation
# -------------------------------------------------


def test_factory_selects_backend(tmp_path):
    from app.core.config import Settings

    local_settings = Settings(
        DATABASE_URL="sqlite:///:memory:",
        SECRET_KEY="x" * 32,
        STORAGE_BACKEND="local",
        STORAGE_DIR=str(tmp_path / "storage"),
    )
    assert isinstance(
        build_object_store(local_settings), LocalObjectStore
    )

    s3_settings = Settings(
        DATABASE_URL="sqlite:///:memory:",
        SECRET_KEY="x" * 32,
        STORAGE_BACKEND="s3",
        S3_ENDPOINT_URL="https://s3.us-west-004.backblazeb2.com",
        S3_BUCKET="vault",
        S3_ACCESS_KEY="key",
        S3_SECRET_KEY="secret",
    )
    assert isinstance(
        build_object_store(s3_settings), S3ObjectStore
    )

    bad_settings = Settings(
        DATABASE_URL="sqlite:///:memory:",
        SECRET_KEY="x" * 32,
        STORAGE_BACKEND="tape",
    )
    with pytest.raises(RuntimeError):
        build_object_store(bad_settings)


def test_s3_store_rejects_missing_config():
    with pytest.raises(RuntimeError) as exc_info:
        S3ObjectStore(
            endpoint_url=None,
            bucket=None,
            access_key=None,
            secret_key=None,
        )

    message = str(exc_info.value)
    assert "S3_ENDPOINT_URL" in message
    assert "S3_BUCKET" in message


# -------------------------------------------------
# Key-shape / traversal safety
# -------------------------------------------------

TRAVERSAL_KEYS = [
    "files/../../etc/passwd",
    "files/..\\..\\windows\\system32",
    "/abs/path.svlt",
    "files/u/f.svlt",
    "tmp/evil.svlt",
    "vault/x.svlt",
    "files/00000000-0000-0000-0000-000000000000/not-a-uuid.svlt",
    "files/00000000-0000-0000-0000-000000000000/00000000-0000-0000-0000-000000000001.txt",
    "",
    "files/00000000-0000-0000-0000-000000000000/"
    "00000000-0000-0000-0000-000000000001.svlt/extra",
]


def test_validate_container_key_unit():
    from app.infrastructure.storage.keys import validate_container_key

    good = (
        "files/12345678-1234-1234-1234-1234567890ab/"
        "abcdef01-2345-6789-abcd-ef0123456789.svlt"
    )
    assert validate_container_key(good) == good

    for bad in TRAVERSAL_KEYS:
        with pytest.raises(ValueError):
            validate_container_key(bad)


def test_s3_traversal_keys_rejected(storage, s3_bucket):
    """A malicious or corrupted storage_path must never become an
    S3 object key: every store-facing operation rejects it, and
    nothing lands in the bucket."""

    for bad in TRAVERSAL_KEYS:
        with pytest.raises(ValueError):
            storage.open_container(bad)
        with pytest.raises(ValueError):
            storage.container_exists(bad)
        with pytest.raises(ValueError):
            storage.container_size(bad)
        with pytest.raises(ValueError):
            storage.delete_container(bad)
        with pytest.raises(ValueError):
            storage.put_container(bad, io.BytesIO(b"x"))
        with pytest.raises(ValueError):
            with storage.write_container(bad):
                pass
        with pytest.raises(ValueError):
            storage.stage_container(bad)

    assert list(storage.iter_container_keys()) == []

    names = [
        obj["Key"]
        for page in s3_bucket.get_paginator("list_objects_v2").paginate(
            Bucket=BUCKET
        )
        for obj in page.get("Contents", [])
    ]
    assert names == []


def test_local_traversal_keys_rejected(tmp_path):
    """Same invariant for the local backend. Note this is stricter
    than the old resolve_path() guard, which allowed any shape that
    stayed under the storage root (e.g. ``tmp/…``); all writer
    paths only ever emit container_key() shapes, so no legitimate
    row is affected."""

    local = StorageService(storage_dir=tmp_path / "storage")

    for bad in TRAVERSAL_KEYS:
        with pytest.raises(ValueError):
            local.open_container(bad)
        with pytest.raises(ValueError):
            local.delete_container(bad)
        with pytest.raises(ValueError):
            local.container_exists(bad)


def test_shape_is_not_ownership(downloader, uploader, user, key, tmp_path):
    """A well-formed key for a *different* user UUID passes shape
    validation (it is a legitimate container address) — access
    control stays at the DB layer, where rows are ownership-scoped."""

    from app.infrastructure.storage.keys import validate_container_key

    source = tmp_path / "owned.txt"
    source.write_text("mine")
    stored = uploader.upload_file(user.id, key, source)

    foreign = f"files/{uuid.uuid4()}/{stored.id}.svlt"
    assert validate_container_key(foreign) == foreign

    # …but the row itself is unreachable to anyone but the owner.
    with pytest.raises(NotFoundError):
        downloader.get_for_user(uuid.uuid4(), stored.id)

    found = downloader.get_for_user(user.id, stored.id)
    assert found.id == stored.id


def test_validate_storage_settings(monkeypatch):
    import app.core.security_settings as sec

    monkeypatch.setattr(
        sec.settings, "STORAGE_BACKEND", "local"
    )
    validate_storage_settings()

    monkeypatch.setattr(sec.settings, "STORAGE_BACKEND", "s3")
    monkeypatch.setattr(sec.settings, "S3_ENDPOINT_URL", None)
    monkeypatch.setattr(sec.settings, "S3_BUCKET", "vault")
    monkeypatch.setattr(sec.settings, "S3_ACCESS_KEY", "key")
    monkeypatch.setattr(sec.settings, "S3_SECRET_KEY", "secret")

    with pytest.raises(RuntimeError) as exc_info:
        validate_storage_settings()

    assert "S3_ENDPOINT_URL" in str(exc_info.value)

    monkeypatch.setattr(
        sec.settings,
        "S3_ENDPOINT_URL",
        "https://s3.us-west-004.backblazeb2.com",
    )
    validate_storage_settings()

    monkeypatch.setattr(
        sec.settings, "STORAGE_BACKEND", "tape"
    )
    with pytest.raises(RuntimeError):
        validate_storage_settings()
