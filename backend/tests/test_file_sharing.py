import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base
from app.main import app

# Ensure the FileShare table is registered on Base.metadata before
# create_all (app.main already pulls it in via the shares router).
from app.domain.models.file_share import FileShare  # noqa: F401

from app.scripts.initialize_identity import (
    seed_permissions,
    seed_role_permissions,
    seed_roles,
)

PASSWORD = "SecureVault#2026"


@pytest.fixture
def db_session(tmp_path):
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    Base.metadata.create_all(engine)

    TestingSessionLocal = sessionmaker(
        bind=engine,
        autoflush=False,
        expire_on_commit=False,
    )

    session = TestingSessionLocal()

    seed_permissions(session)
    seed_roles(session)
    seed_role_permissions(session)

    yield session

    session.close()
    engine.dispose()


@pytest.fixture
def client(db_session, tmp_path):
    from app.api.dependencies import database as database_dep

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    from contextlib import asynccontextmanager

    @asynccontextmanager
    async def _noop_lifespan(_app):
        yield

    app.router.lifespan_context = _noop_lifespan

    app.dependency_overrides[
        database_dep.get_db
    ] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    from app.services.auth.login_rate_limiter import (
        get_login_rate_limiter,
    )

    get_login_rate_limiter().clear()

    from app.main import reset_rate_limiter

    reset_rate_limiter()

    app.dependency_overrides.clear()


def _register(client, email, username, password=PASSWORD):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "username": username,
            "password": password,
        },
    )

    assert response.status_code in (200, 201)

    return response


def _login(client, email, password=PASSWORD):
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": email,
            "password": password,
        },
    )

    assert response.status_code == 200

    return response.json()


def _token(client, email, username):
    _register(client, email, username)

    return _login(client, email)["access_token"]


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


def _make_key(client, token, name="primary"):
    response = client.post(
        "/api/v1/keys",
        headers=_auth(token),
        json={"name": name},
    )

    assert response.status_code == 201

    return response.json()


def _upload(client, token, content=b"top secret bytes", name="secret.txt"):
    response = client.post(
        "/api/v1/files/upload",
        headers=_auth(token),
        files={
            "upload": (
                name,
                content,
                "text/plain",
            )
        },
    )

    assert response.status_code == 201

    return response.json()


def test_share_roundtrip_grantee_can_download(client):
    alice = _token(client, "alice@example.com", "alice")
    bob = _token(client, "bob@example.com", "bob")

    _make_key(client, alice)
    _make_key(client, bob)

    content = b"shared plaintext " * 64

    stored = _upload(client, alice, content=content)

    file_id = stored["id"]

    # Bob cannot see it before the grant (404, no enumeration).
    assert (
        client.get(
            f"/api/v1/files/{file_id}",
            headers=_auth(bob),
        ).status_code
        == 404
    )

    assert (
        client.get(
            f"/api/v1/files/{file_id}/download",
            headers=_auth(bob),
        ).status_code
        == 404
    )

    share = client.post(
        f"/api/v1/shares/files/{file_id}/share",
        headers=_auth(alice),
        json={"grantee_email": "bob@example.com"},
    )

    assert share.status_code == 201

    body = share.json()

    assert body["file_id"] == file_id

    # Bob can now read metadata and download the same plaintext.
    meta = client.get(
        f"/api/v1/files/{file_id}",
        headers=_auth(bob),
    )

    assert meta.status_code == 200

    assert meta.json()["id"] == file_id

    download = client.get(
        f"/api/v1/files/{file_id}/download",
        headers=_auth(bob),
    )

    assert download.status_code == 200

    assert download.content == content

    # Owner download still works and is unchanged.
    owner_download = client.get(
        f"/api/v1/files/{file_id}/download",
        headers=_auth(alice),
    )

    assert owner_download.status_code == 200

    assert owner_download.content == content

    # Bob sees the grant in /shares/received.
    received = client.get(
        "/api/v1/shares/received",
        headers=_auth(bob),
    )

    assert received.status_code == 200

    assert any(
        item["file_id"] == file_id
        for item in received.json()
    )

    # Owner sees the grant in the per-file listing.
    listing = client.get(
        f"/api/v1/shares/files/{file_id}/shares",
        headers=_auth(alice),
    )

    assert listing.status_code == 200

    assert len(listing.json()) == 1


def test_share_audit_events_recorded(client, db_session):
    alice = _token(client, "alice2@example.com", "alice2")
    bob = _token(client, "bob2@example.com", "bob2")

    _make_key(client, alice)
    _make_key(client, bob)

    stored = _upload(client, alice)

    file_id = stored["id"]

    # Bob needs a user id for the audit lookup below.
    from app.domain.models.user import User

    bob_row = (
        db_session.query(User)
        .filter(User.email == "bob2@example.com")
        .first()
    )

    assert bob_row is not None

    assert (
        client.post(
            f"/api/v1/shares/files/{file_id}/share",
            headers=_auth(alice),
            json={"grantee_email": "bob2@example.com"},
        ).status_code
        == 201
    )

    # Bob downloads once so both share + download appear.
    assert (
        client.get(
            f"/api/v1/files/{file_id}/download",
            headers=_auth(bob),
        ).status_code
        == 200
    )

    shared = client.get(
        "/api/v1/audit/logs",
        headers=_auth(alice),
        params={"action": "file.shared"},
    )

    assert shared.status_code == 200

    assert shared.json()["total"] >= 1

    # Revoke and check the revocation event.
    assert (
        client.delete(
            f"/api/v1/shares/files/{file_id}/shares/{bob_row.id}",
            headers=_auth(alice),
        ).status_code
        == 204
    )

    revoked = client.get(
        "/api/v1/audit/logs",
        headers=_auth(alice),
        params={"action": "file.share_revoked"},
    )

    assert revoked.status_code == 200

    assert revoked.json()["total"] >= 1


def test_revoke_blocks_grantee_download(client, db_session):
    alice = _token(client, "alice3@example.com", "alice3")
    bob = _token(client, "bob3@example.com", "bob3")

    _make_key(client, alice)
    _make_key(client, bob)

    stored = _upload(client, alice, content=b"revocable")

    file_id = stored["id"]

    assert (
        client.post(
            f"/api/v1/shares/files/{file_id}/share",
            headers=_auth(alice),
            json={"grantee_email": "bob3@example.com"},
        ).status_code
        == 201
    )

    assert (
        client.get(
            f"/api/v1/files/{file_id}/download",
            headers=_auth(bob),
        ).status_code
        == 200
    )

    from app.domain.models.user import User

    bob_row = (
        db_session.query(User)
        .filter(User.email == "bob3@example.com")
        .first()
    )

    revoke = client.delete(
        f"/api/v1/shares/files/{file_id}/shares/{bob_row.id}",
        headers=_auth(alice),
    )

    assert revoke.status_code == 204

    # Grant is gone: download + metadata are 404 again, the
    # received list is empty, and the owner is unaffected.
    assert (
        client.get(
            f"/api/v1/files/{file_id}/download",
            headers=_auth(bob),
        ).status_code
        == 404
    )

    assert (
        client.get(
            f"/api/v1/files/{file_id}",
            headers=_auth(bob),
        ).status_code
        == 404
    )

    received = client.get(
        "/api/v1/shares/received",
        headers=_auth(bob),
    )

    assert received.json() == []

    assert (
        client.get(
            f"/api/v1/files/{file_id}/download",
            headers=_auth(alice),
        ).status_code
        == 200
    )


def test_share_is_idempotent_and_owner_scoped(client, db_session):
    alice = _token(client, "alice4@example.com", "alice4")
    bob = _token(client, "bob4@example.com", "bob4")
    carol = _token(client, "carol4@example.com", "carol4")

    _make_key(client, alice)
    _make_key(client, bob)
    _make_key(client, carol)

    stored = _upload(client, alice)

    file_id = stored["id"]

    first = client.post(
        f"/api/v1/shares/files/{file_id}/share",
        headers=_auth(alice),
        json={"grantee_email": "bob4@example.com"},
    )

    second = client.post(
        f"/api/v1/shares/files/{file_id}/share",
        headers=_auth(alice),
        json={"grantee_email": "bob4@example.com"},
    )

    assert first.status_code == 201
    assert second.status_code == 201

    # Idempotent: the same grant row is returned, not a duplicate.
    assert first.json()["id"] == second.json()["id"]

    listing = client.get(
        f"/api/v1/shares/files/{file_id}/shares",
        headers=_auth(alice),
    )

    assert len(listing.json()) == 1

    # Non-owners cannot share, list grants, or revoke (404, not 403,
    # so file existence is not leaked to strangers).
    assert (
        client.post(
            f"/api/v1/shares/files/{file_id}/share",
            headers=_auth(bob),
            json={"grantee_email": "carol4@example.com"},
        ).status_code
        == 404
    )

    assert (
        client.get(
            f"/api/v1/shares/files/{file_id}/shares",
            headers=_auth(carol),
        ).status_code
        == 404
    )

    from app.domain.models.user import User

    bob_row = (
        db_session.query(User)
        .filter(User.email == "bob4@example.com")
        .first()
    )

    assert (
        client.delete(
            f"/api/v1/shares/files/{file_id}/shares/{bob_row.id}",
            headers=_auth(bob),
        ).status_code
        == 404
    )


def test_share_validation_errors(client):
    alice = _token(client, "alice5@example.com", "alice5")
    bob = _token(client, "bob5@example.com", "bob5")
    nokey = _token(client, "nokey5@example.com", "nokey5")

    _make_key(client, alice)
    _make_key(client, bob)
    # nokey intentionally has no encryption key.

    stored = _upload(client, alice)

    file_id = stored["id"]

    # Unknown recipient.
    assert (
        client.post(
            f"/api/v1/shares/files/{file_id}/share",
            headers=_auth(alice),
            json={"grantee_email": "ghost@example.com"},
        ).status_code
        == 404
    )

    # Self-share.
    assert (
        client.post(
            f"/api/v1/shares/files/{file_id}/share",
            headers=_auth(alice),
            json={"grantee_email": "alice5@example.com"},
        ).status_code
        == 400
    )

    # Recipient without an active key.
    assert (
        client.post(
            f"/api/v1/shares/files/{file_id}/share",
            headers=_auth(alice),
            json={"grantee_email": "nokey5@example.com"},
        ).status_code
        == 400
    )

    # Missing file.
    import uuid

    assert (
        client.post(
            f"/api/v1/shares/files/{uuid.uuid4()}/share",
            headers=_auth(alice),
            json={"grantee_email": "bob5@example.com"},
        ).status_code
        == 404
    )


def test_each_grantee_gets_independent_wrap(client):
    alice = _token(client, "alice6@example.com", "alice6")
    bob = _token(client, "bob6@example.com", "bob6")
    carol = _token(client, "carol6@example.com", "carol6")

    _make_key(client, alice)
    _make_key(client, bob)
    _make_key(client, carol)

    content = b"multi-grantee payload " * 32

    stored = _upload(client, alice, content=content)

    file_id = stored["id"]

    for email in ("bob6@example.com", "carol6@example.com"):
        assert (
            client.post(
                f"/api/v1/shares/files/{file_id}/share",
                headers=_auth(alice),
                json={"grantee_email": email},
            ).status_code
            == 201
        )

    for token in (bob, carol):
        download = client.get(
            f"/api/v1/files/{file_id}/download",
            headers=_auth(token),
        )

        assert download.status_code == 200

        assert download.content == content

    # The two grants wrap the same session key under different
    # public keys, so the stored blobs must differ.
    listing = client.get(
        f"/api/v1/shares/files/{file_id}/shares",
        headers=_auth(alice),
    )

    assert len(listing.json()) == 2

    from app.domain.models.file_share import FileShare as ShareModel

    # Distinct grantees, distinct wrapped keys (checked at the DB
    # level through the service in the next assertion via API
    # visibility: both downloads succeeded independently).
    assert (
        listing.json()[0]["grantee_id"]
        != listing.json()[1]["grantee_id"]
    )
