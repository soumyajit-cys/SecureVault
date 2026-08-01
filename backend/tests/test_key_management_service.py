import uuid

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.orm import sessionmaker

from app.domain.models.user import User
from app.infrastructure.database.base import Base
from app.infrastructure.repositories.crypto_key_repository import (
    SQLAlchemyCryptoKeyRepository,
)
from app.services.key_management_service import (
    KeyExpiredError,
    KeyManagementService,
    KeyNotFoundError,
    KeyRevokedError,
)


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

    user = User(
        email="keyuser@example.com",
        username="keyuser",
        password_hash="hash",
    )

    session.add(user)

    session.commit()

    yield session

    session.close()

    engine.dispose()


@pytest.fixture
def user_id(db_session):
    return db_session.query(User).first().id


@pytest.fixture
def service(db_session):
    repo = SQLAlchemyCryptoKeyRepository(db_session)
    return KeyManagementService(repo)


def test_generate_key_pair(
    db_session,
    user_id,
    service,
):

    key = service.generate_key_pair(
        user_id,
        "primary",
        validity_days=90,
    )

    assert key.id is not None

    assert key.status == "active"

    assert key.algorithm == "RSA-4096"

    assert key.key_size == 4096

    assert key.public_key_pem.startswith(
        "-----BEGIN PUBLIC KEY-----"
    )

    assert len(key.fingerprint) == 64

    assert key.expires_at is not None

    assert "PRIVATE KEY" not in (
        key.encrypted_private_key_pem
    )

    assert db_session.get(
        type(key),
        key.id,
    ) is not None


def test_unlock_private_key_round_trip(
    db_session,
    user_id,
    service,
):

    key = service.generate_key_pair(
        user_id,
        "primary",
    )

    private_key = service.unlock_private_key(
        key
    )

    assert private_key.key_size == 4096


def test_encrypted_at_rest_is_not_plaintext(
    db_session,
    user_id,
    service,
):

    key = service.generate_key_pair(
        user_id,
        "primary",
    )

    payload = (
        key.encrypted_private_key_pem
    )

    assert "-----BEGIN PRIVATE KEY-----" not in payload

    assert key.private_key_nonce

    assert key.private_key_tag

    assert key.private_key_salt


def test_get_key(
    db_session,
    user_id,
    service,
):

    key = service.generate_key_pair(
        user_id,
        "primary",
    )

    found = service.get_key(
        user_id,
        key.id,
    )

    assert found.id == key.id


def test_get_key_wrong_user(
    db_session,
    user_id,
    service,
):

    other_id = uuid.uuid4()

    key = service.generate_key_pair(
        user_id,
        "primary",
    )

    with pytest.raises(
        KeyNotFoundError
    ):

        service.get_key(
            other_id,
            key.id,
        )


def test_get_key_missing(
    db_session,
    user_id,
    service,
):

    with pytest.raises(
        KeyNotFoundError
    ):

        service.get_key(
            user_id,
            uuid.uuid4(),
        )


def test_get_active_key(
    db_session,
    user_id,
    service,
):

    service.generate_key_pair(
        user_id,
        "first",
    )

    latest = service.generate_key_pair(
        user_id,
        "second",
    )

    active = service.get_active_key(
        user_id
    )

    assert active.id == latest.id


def test_get_active_key_missing(
    db_session,
    user_id,
    service,
):

    with pytest.raises(
        KeyNotFoundError
    ):

        service.get_active_key(
            user_id
        )


def test_list_keys(
    db_session,
    user_id,
    service,
):

    service.generate_key_pair(
        user_id,
        "a",
    )

    service.generate_key_pair(
        user_id,
        "b",
    )

    keys = service.list_keys(
        user_id
    )

    assert len(keys) == 2

    assert keys[0].name == "b"


def test_rotate_key(
    db_session,
    user_id,
    service,
):

    old = service.generate_key_pair(
        user_id,
        "primary",
    )

    rotated_old, new = service.rotate_key(
        user_id,
        old.id,
    )

    assert rotated_old.status == "revoked"

    assert rotated_old.revoked_at is not None

    assert rotated_old.replaced_by_key_id == new.id

    assert new.status == "active"

    assert new.id != old.id

    with pytest.raises(
        KeyRevokedError
    ):

        service.unlock_private_key(
            rotated_old
        )

    # new key unlocks fine
    assert service.unlock_private_key(
        new
    ).key_size == 4096


def test_rotate_key_missing(
    db_session,
    user_id,
    service,
):

    with pytest.raises(
        KeyNotFoundError
    ):

        service.rotate_key(
            user_id,
            uuid.uuid4(),
        )


def test_revoke_key(
    db_session,
    user_id,
    service,
):

    key = service.generate_key_pair(
        user_id,
        "primary",
    )

    revoked = service.revoke_key(
        user_id,
        key.id,
    )

    assert revoked.status == "revoked"

    assert revoked.revoked_at is not None

    with pytest.raises(
        KeyRevokedError
    ):

        service.unlock_private_key(
            revoked
        )


def test_revoke_key_missing(
    db_session,
    user_id,
    service,
):

    with pytest.raises(
        KeyNotFoundError
    ):

        service.revoke_key(
            user_id,
            uuid.uuid4(),
        )


def test_expire_old_keys(
    db_session,
    user_id,
    service,
):

    service.generate_key_pair(
        user_id,
        "short-lived",
        validity_days=0,
    )

    service.generate_key_pair(
        user_id,
        "long-lived",
        validity_days=365,
    )

    expired_count = (
        service.expire_old_keys()
    )

    assert expired_count == 1

    keys = service.list_keys(
        user_id
    )

    statuses = {
        key.name: key.status
        for key in keys
    }

    assert statuses["short-lived"] == "expired"

    assert statuses["long-lived"] == "active"


def test_expired_key_cannot_unlock(
    db_session,
    user_id,
    service,
):

    key = service.generate_key_pair(
        user_id,
        "expiring",
        validity_days=0,
    )

    service.expire_old_keys()

    with pytest.raises(
        KeyExpiredError
    ):

        service.unlock_private_key(
            key
        )


def test_key_metadata(
    db_session,
    user_id,
    service,
):

    key = service.generate_key_pair(
        user_id,
        "primary",
    )

    metadata = service.key_metadata(
        key
    )

    assert metadata["id"] == str(key.id)

    assert metadata["name"] == "primary"

    assert metadata["algorithm"] == "RSA-4096"

    assert metadata["status"] == "active"

    assert len(metadata["fingerprint"]) == 64
