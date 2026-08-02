import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base
from app.main import app
from app.scripts.initialize_identity import (
    seed_permissions,
    seed_roles,
)


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

    yield session

    session.close()

    engine.dispose()


@pytest.fixture
def client(
    db_session,
    tmp_path,
):

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

    # Disable the production lifespan (e.g. security data seeding,
    # background garbage collection) which would touch PostgreSQL.
    app.router.lifespan_context = _noop_lifespan

    app.dependency_overrides[
        database_dep.get_db
    ] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def user_token(client):
    """
    Register and log in a standard user; returns its bearer token.
    """

    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "api@example.com",
            "username": "apiuser",
            "password": "SecureVault#2026",
        },
    )

    assert response.status_code in (200, 201)

    login = client.post(
        "/api/v1/auth/login",
        json={
            "email": "api@example.com",
            "username": "apiuser",
            "password": "SecureVault#2026",
        },
    )

    assert login.status_code == 200

    return login.json()["access_token"]


def test_health(client):

    response = client.get("/api/v1/health")

    assert response.status_code == 200

    assert response.json()["status"] == "healthy"


def test_register_login_flow(client):

    r = client.post(
        "/api/v1/auth/register",
        json={
            "email": "flow@example.com",
            "username": "flowuser",
            "password": "SecureVault#2026",
        },
    )

    assert r.status_code == 200

    l = client.post(
        "/api/v1/auth/login",
        json={
            "email": "flow@example.com",
            "username": "flowuser",
            "password": "SecureVault#2026",
        },
    )

    assert l.status_code == 200

    assert "access_token" in l.json()

    assert "refresh_token" in l.json()


def test_key_lifecycle(client, user_token):

    headers = {
        "Authorization": f"Bearer {user_token}"
    }

    generate = client.post(
        "/api/v1/keys",
        headers=headers,
        json={
            "name": "primary",
            "validity_days": 90,
        },
    )

    assert generate.status_code == 201

    data = generate.json()

    assert data["status"] == "active"

    assert data["public_key_pem"].startswith(
        "-----BEGIN PUBLIC KEY-----"
    )

    key_id = data["id"]

    listing = client.get(
        "/api/v1/keys",
        headers=headers,
    )

    assert listing.status_code == 200

    assert listing.json()["total"] == 1

    rotate = client.post(
        "/api/v1/keys/rotate",
        headers=headers,
        json={
            "current_key_id": key_id,
        },
    )

    assert rotate.status_code == 200

    assert rotate.json()["old_key"]["status"] == "revoked"

    new_key_id = rotate.json()["new_key"]["id"]

    revoke = client.post(
        f"/api/v1/keys/{new_key_id}/revoke",
        headers=headers,
    )

    assert revoke.status_code == 200

    assert revoke.json()["revoked"] is True


def test_text_encrypt_decrypt_round_trip(client, user_token):
    headers = {
        "Authorization": f"Bearer {user_token}"
    }

    client.post(
        "/api/v1/keys",
        headers=headers,
        json={"name": "primary"},
    )

    enc = client.post(
        "/api/v1/encryption/text/encrypt",
        headers=headers,
        json={
            "plaintext": "hello SecureVault"
        },
    )

    assert enc.status_code == 200

    payload = enc.json()

    dec = client.post(
        "/api/v1/encryption/text/decrypt",
        headers=headers,
        json={
            "nonce": payload["nonce"],
            "ciphertext": payload["ciphertext"],
            "tag": payload["tag"],
            "encrypted_key": payload["encrypted_key"],
        },
    )

    assert dec.status_code == 200

    assert dec.json()["plaintext"] == "hello SecureVault"


def test_file_upload_download_roundtrip(client, user_token, tmp_path):
    headers = {
        "Authorization": f"Bearer {user_token}"
    }

    client.post(
        "/api/v1/keys",
        headers=headers,
        json={"name": "primary"},
    )

    upload = client.post(
        "/api/v1/files/upload",
        headers=headers,
        files={
            "upload": (
                "secret.txt",
                b"SecureVault file content" * 100,
                "text/plain",
            )
        },
    )

    assert upload.status_code == 201

    data = upload.json()

    assert data["original_filename"] == "secret.txt"

    file_id = data["id"]

    listing = client.get(
        "/api/v1/files",
        headers=headers,
    )

    assert listing.status_code == 200

    assert listing.json()["total"] == 1

    download = client.get(
        f"/api/v1/files/{file_id}/download",
        headers=headers,
    )

    assert download.status_code == 200

    assert b"SecureVault file content" in download.content

    delete = client.delete(
        f"/api/v1/files/{file_id}",
        headers=headers,
    )

    assert delete.status_code == 204


def test_audit_logs(client, user_token):
    headers = {
        "Authorization": f"Bearer {user_token}"
    }

    logs = client.get(
        "/api/v1/audit/logs",
        headers=headers,
    )

    assert logs.status_code == 200

    assert "total" in logs.json()


def test_profile(client, user_token):
    headers = {
        "Authorization": f"Bearer {user_token}"
    }

    me = client.get(
        "/api/v1/profile/me",
        headers=headers,
    )

    assert me.status_code == 200

    assert me.json()["email"] == "api@example.com"


def test_unauthorized_access_rejected(client):

    response = client.get(
        "/api/v1/profile/me"
    )

    assert response.status_code == 401