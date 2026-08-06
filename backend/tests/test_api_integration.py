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

    from app.services.auth.login_rate_limiter import (
        get_login_rate_limiter,
    )

    get_login_rate_limiter().clear()

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


def test_liveness(client):

    response = client.get(
        "/api/v1/health/live"
    )

    assert response.status_code == 200

    assert (
        response.json()["status"]
        == "healthy"
    )


def test_metrics(client):

    response = client.get(
        "/api/v1/metrics"
    )

    assert response.status_code == 200

    assert (
        "vault_requests_total"
        in response.text
    )


def test_security_headers(client):

    response = client.get(
        "/api/v1/health"
    )

    assert (
        response.headers.get(
            "X-Content-Type-Options"
        )
        == "nosniff"
    )


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


def test_change_password_flow(client, user_token):
    headers = {
        "Authorization": f"Bearer {user_token}"
    }

    changed = client.post(
        "/api/v1/auth/change-password",
        headers=headers,
        json={
            "current_password": "SecureVault#2026",
            "new_password": "NewSecureVault#2027",
        },
    )

    assert changed.status_code == 200

    assert changed.json()["changed"] is True

    stale = client.post(
        "/api/v1/auth/login",
        json={
            "email": "api@example.com",
            "password": "SecureVault#2026",
        },
    )

    assert stale.status_code == 401

    fresh = client.post(
        "/api/v1/auth/login",
        json={
            "email": "api@example.com",
            "password": "NewSecureVault#2027",
        },
    )

    assert fresh.status_code == 200


def test_files_summary(client, user_token):
    headers = {
        "Authorization": f"Bearer {user_token}"
    }

    client.post(
        "/api/v1/keys",
        headers=headers,
        json={"name": "primary"},
    )

    client.post(
        "/api/v1/files/upload",
        headers=headers,
        files={
            "upload": (
                "sum.txt",
                b"x" * 4096,
                "text/plain",
            )
        },
    )

    summary = client.get(
        "/api/v1/files/summary",
        headers=headers,
    )

    assert summary.status_code == 200

    body = summary.json()

    assert body["file_count"] == 1

    assert body["original_bytes"] == 4096

    assert body["encrypted_bytes"] > 0


@pytest.fixture
def admin_token(client, db_session):
    """
    Register a user and promote them to the Admin role.
    """

    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "boss@example.com",
            "username": "boss",
            "password": "SecureVault#2026",
        },
    )

    assert response.status_code == 200

    from app.domain.models.user import User
    from app.domain.models.role import Role
    from app.domain.models.user_role import UserRole

    user = (
        db_session.query(User)
        .filter(User.email == "boss@example.com")
        .first()
    )

    admin_role = (
        db_session.query(Role)
        .filter(Role.name == "Admin")
        .first()
    )

    user.roles.append(
        UserRole(role=admin_role)
    )

    db_session.commit()

    login = client.post(
        "/api/v1/auth/login",
        json={
            "email": "boss@example.com",
            "password": "SecureVault#2026",
        },
    )

    assert login.status_code == 200

    return login.json()["access_token"]


def test_admin_user_management(client, user_token, admin_token):
    admin_headers = {
        "Authorization": f"Bearer {admin_token}"
    }

    users = client.get(
        "/api/v1/admin/users",
        headers=admin_headers,
    )

    assert users.status_code == 200

    body = users.json()

    assert body["total"] >= 2

    victim = next(
        u for u in body["items"]
        if u["email"] == "api@example.com"
    )

    deactivate = client.post(
        f"/api/v1/admin/users/{victim['id']}/deactivate",
        headers=admin_headers,
    )

    assert deactivate.status_code == 200

    blocked = client.post(
        "/api/v1/auth/login",
        json={
            "email": "api@example.com",
            "password": "SecureVault#2026",
        },
    )

    assert blocked.status_code == 401

    activate = client.post(
        f"/api/v1/admin/users/{victim['id']}/activate",
        headers=admin_headers,
    )

    assert activate.status_code == 200

    allowed = client.post(
        "/api/v1/auth/login",
        json={
            "email": "api@example.com",
            "password": "SecureVault#2026",
        },
    )

    assert allowed.status_code == 200


def test_admin_endpoint_requires_admin(client, user_token):
    headers = {
        "Authorization": f"Bearer {user_token}"
    }

    forbidden = client.get(
        "/api/v1/admin/users",
        headers=headers,
    )

    assert forbidden.status_code == 403


def test_admin_storage_usage(client, admin_token):
    headers = {
        "Authorization": f"Bearer {admin_token}"
    }

    usage = client.get(
        "/api/v1/admin/storage",
        headers=headers,
    )

    assert usage.status_code == 200

    assert "storage_bytes" in usage.json()

    assert "temp_file_count" in usage.json()


def test_folder_archive_flow(client, user_token, tmp_path):
    headers = {
        "Authorization": f"Bearer {user_token}"
    }

    client.post(
        "/api/v1/keys",
        headers=headers,
        json={"name": "primary"},
    )

    archive = tmp_path / "docs.zip"
    import zipfile

    with zipfile.ZipFile(archive, "w") as z:
        z.writestr("readme.txt", "one")
        z.writestr("nested/config.toml", "two")

    upload = client.post(
        "/api/v1/folders/upload",
        headers=headers,
        files={
            "upload": (
                "arch.zip",
                archive.read_bytes(),
                "application/zip",
            )
        },
    )

    assert upload.status_code == 201

    payload = upload.json()

    assert payload["file_count"] == 2

    listing = client.get(
        "/api/v1/folders",
        headers=headers,
    )

    assert listing.status_code == 200

    assert listing.json()["total"] >= 1

    folder_id = client.get(
        "/api/v1/folders",
        headers=headers,
    ).json()["items"][0]["id"]

    restored = client.post(
        f"/api/v1/folders/{folder_id}/restore",
        headers=headers,
    )

    assert restored.status_code == 200

    body = restored.json()

    assert body["restored_files"] >= 2

    from pathlib import Path

    restored_root = Path(body["restored_path"])

    assert (restored_root / "readme.txt").exists()

    assert (restored_root / "nested" / "config.toml").exists()