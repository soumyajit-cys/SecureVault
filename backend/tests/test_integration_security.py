"""
Phase 8 integration tests: authentication lifecycle, token
rotation/replay, MFA enforcement, RBAC mutation, object-ownership
(IDOR) protection, and key lifecycle behaviour.

These tests exercise the full HTTP API against an in-memory
PostgreSQL-compatible SQLite database with seeded identity data,
mirroring the fixture pattern used across the suite.
"""

from datetime import timedelta

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


def _register(
    client,
    email: str,
    username: str,
    password: str = PASSWORD,
):

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


def _login(
    client,
    email: str,
    password: str = PASSWORD,
) -> dict:

    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": email,
            "password": password,
        },
    )

    assert response.status_code == 200

    return response.json()


def _auth(email: str, token: str) -> dict:
    return {
        "Authorization": f"Bearer {token}"
    }


def _enable_totp(
    client,
    token: str,
) -> None:
    """
    Enable TOTP for the given session so privileged
    (Admin/Auditor) users clear the MFA boundary.
    """

    setup = client.post(
        "/api/v1/auth/mfa/setup",
        headers=_auth("mfa-boundary", token),
    )

    assert setup.status_code == 200

    secret = setup.json()["secret"]

    import pyotp

    enabled = client.post(
        "/api/v1/auth/mfa/enable",
        headers=_auth("mfa-boundary", token),
        json={
            "secret": secret,
            "code": pyotp.TOTP(secret).now(),
        },
    )

    assert enabled.status_code == 200


def _refresh(
    client,
    refresh_token: str | None = None,
):
    """
    Cookie-path refresh (CSRF header from the jar) when
    no token is given; body-path refresh otherwise. Call
    client.cookies.clear() first to force the body path.
    """

    headers = {}

    if client.cookies.get("sv_csrf"):
        headers["X-CSRF-Token"] = (
            client.cookies.get("sv_csrf")
        )

    body = {}

    if refresh_token is not None:
        body["refresh_token"] = refresh_token

    return client.post(
        "/api/v1/auth/refresh",
        json=body,
        headers=headers,
    )


def _promote(
    db_session,
    email: str,
    role_name: str,
):
    """
    Attach a role directly to the given user row.
    """

    from app.domain.models.role import Role
    from app.domain.models.user import User
    from app.domain.models.user_role import UserRole

    user = (
        db_session.query(User)
        .filter(User.email == email)
        .first()
    )

    role = (
        db_session.query(Role)
        .filter(Role.name == role_name)
        .first()
    )

    user.roles.append(
        UserRole(role=role)
    )

    db_session.commit()


# -------------------------------------------------
# 8.1 Authentication lifecycle
# -------------------------------------------------

def test_expired_access_token_rejected(
    client,
    db_session,
):

    _register(
        client,
        "expired@example.com",
        "expireduser",
    )

    login = _login(
        client,
        "expired@example.com",
    )

    from app.infrastructure.repositories.jwt_signing_key_repository import (
        SQLAlchemyJwtSigningKeyRepository,
    )
    from app.services.auth.jwt_key_service import (
        JwtKeyService,
    )
    from app.services.auth.jwt_service import (
        JWTService,
    )

    jwt_service = JWTService(
        JwtKeyService(
            SQLAlchemyJwtSigningKeyRepository(
                db_session
            )
        )
    )

    claims = jwt_service.decode_token(
        login["access_token"]
    )

    expired = jwt_service.create_token(
        {
            "sub": claims.sub,
            "email": claims.email,
            "session_id": claims.session_id,
            "token_type": "access",
        },
        timedelta(seconds=-60),
    )

    response = client.get(
        "/api/v1/auth/mfa/status",
        headers=_auth(
            "expired@example.com",
            expired,
        ),
    )

    assert response.status_code == 401


def test_refresh_token_rotation_invalidates_old_token(
    client,
):

    _register(
        client,
        "rotate@example.com",
        "rotateuser",
    )

    _login(
        client,
        "rotate@example.com",
    )

    rotated_cookie = (
        client.cookies.get(
            "sv_refresh"
        )
    )

    first = _refresh(
        client,
    )

    assert first.status_code == 200

    assert (
        client.cookies.get(
            "sv_refresh"
        )
        != rotated_cookie
    )

    # Replay the pre-rotation token through the body
    # path: rotation invalidated it.
    client.cookies.clear()

    replay = _refresh(
        client,
        rotated_cookie,
    )

    assert replay.status_code == 401


def test_replayed_refresh_token_revokes_whole_family(
    client,
):

    _register(
        client,
        "family@example.com",
        "familyuser",
    )

    _login(
        client,
        "family@example.com",
    )

    pre_rotation = (
        client.cookies.get(
            "sv_refresh"
        )
    )

    first = _refresh(
        client,
    )

    assert first.status_code == 200

    post_rotation = (
        client.cookies.get(
            "sv_refresh"
        )
    )

    assert post_rotation != pre_rotation

    # Replay the pre-rotation token: the family is
    # poisoned, so this must fail.
    client.cookies.clear()

    replay = _refresh(
        client,
        pre_rotation,
    )

    assert replay.status_code == 401

    # The rotated token belongs to the same family;
    # the replay must have poisoned it too.
    second = _refresh(
        client,
        post_rotation,
    )

    assert second.status_code == 401


def test_logout_revokes_refresh_token(client):

    _register(
        client,
        "logout@example.com",
        "logoutuser",
    )

    _login(
        client,
        "logout@example.com",
    )

    current = (
        client.cookies.get(
            "sv_refresh"
        )
    )

    logout = client.post(
        "/api/v1/auth/logout",
        json={},
        headers={
            "X-CSRF-Token": (
                client.cookies.get(
                    "sv_csrf"
                )
            )
        },
    )

    assert logout.status_code == 200

    assert (
        "sv_refresh"
        not in client.cookies
    )

    refresh = _refresh(
        client,
        current,
    )

    assert refresh.status_code == 401


def test_refresh_rejects_access_token_type(client):

    _register(
        client,
        "wrongtype@example.com",
        "wrongtype",
    )

    login = _login(
        client,
        "wrongtype@example.com",
    )

    client.cookies.clear()

    response = _refresh(
        client,
        login["access_token"],
    )

    assert response.status_code == 401


def test_invalid_credentials_rejected(client):

    _register(
        client,
        "badpass@example.com",
        "badpass",
    )

    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "badpass@example.com",
            "password": "WrongPassword#2026",
        },
    )

    assert response.status_code == 401


# -------------------------------------------------
# 8.2 MFA enforcement
# -------------------------------------------------

def test_mfa_enforced_login_issues_no_access_token(
    client,
):

    _register(
        client,
        "enforced@example.com",
        "enforced",
    )

    token = _login(
        client,
        "enforced@example.com",
    )["access_token"]

    import pyotp

    setup = client.post(
        "/api/v1/auth/mfa/setup",
        headers=_auth("enforced@example.com", token),
    )

    assert setup.status_code == 200

    secret = setup.json()["secret"]

    enable = client.post(
        "/api/v1/auth/mfa/enable",
        headers=_auth("enforced@example.com", token),
        json={
            "secret": secret,
            "code": pyotp.TOTP(secret).now(),
        },
    )

    assert enable.status_code == 200

    login = client.post(
        "/api/v1/auth/login",
        json={
            "email": "enforced@example.com",
            "password": PASSWORD,
        },
    )

    assert login.status_code == 200

    body = login.json()

    assert body["mfa_required"] is True

    assert "access_token" not in body

    assert "refresh_token" not in body

    assert "mfa_token" in body

    # The unverified mfa_token must not grant access.
    profile = client.get(
        "/api/v1/profile/me",
        headers=_auth(
            "enforced@example.com",
            body["mfa_token"],
        ),
    )

    assert profile.status_code == 401


# -------------------------------------------------
# 8.3 RBAC mutation
# -------------------------------------------------

def test_role_removal_revokes_admin_access(
    client,
    db_session,
):

    _register(
        client,
        "demote@example.com",
        "demote",
    )

    _promote(
        db_session,
        "demote@example.com",
        "Admin",
    )

    admin_token = _login(
        client,
        "demote@example.com",
    )["access_token"]

    _enable_totp(client, admin_token)

    admin_call = client.get(
        "/api/v1/admin/users",
        headers=_auth(
            "demote@example.com",
            admin_token,
        ),
    )

    assert admin_call.status_code == 200

    from app.domain.models.role import Role
    from app.domain.models.user import User

    user = (
        db_session.query(User)
        .filter(User.email == "demote@example.com")
        .first()
    )

    admin_role = (
        db_session.query(Role)
        .filter(Role.name == "Admin")
        .first()
    )

    user.roles = [
        membership
        for membership in user.roles
        if membership.role_id != admin_role.id
    ]

    db_session.commit()

    revoked_call = client.get(
        "/api/v1/admin/users",
        headers=_auth(
            "demote@example.com",
            admin_token,
        ),
    )

    assert revoked_call.status_code == 403


def test_auditor_role_cannot_use_admin_endpoints(
    client,
    db_session,
):

    _register(
        client,
        "auditor@example.com",
        "auditor",
    )

    _promote(
        db_session,
        "auditor@example.com",
        "Auditor",
    )

    token = _login(
        client,
        "auditor@example.com",
    )["access_token"]

    users = client.get(
        "/api/v1/admin/users",
        headers=_auth("auditor@example.com", token),
    )

    assert users.status_code == 403

    storage = client.get(
        "/api/v1/admin/storage",
        headers=_auth("auditor@example.com", token),
    )

    assert storage.status_code == 403


def _generate_key(
    client,
    token: str,
    name: str = "idorendpoint-key",
):
    """
    Create an encryption key for the given user so
    uploads have a key to seal containers with.
    """

    response = client.post(
        "/api/v1/keys",
        headers=_auth("owner@example.com", token),
        json={
            "name": name,
            "validity_days": 365,
        },
    )

    assert response.status_code == 201


# -------------------------------------------------
# 8.4 Object ownership (IDOR)
# -------------------------------------------------

def test_cross_user_file_access_denied(
    client,
):

    _register(
        client,
        "owner@example.com",
        "owner",
    )

    _register(
        client,
        "other@example.com",
        "other",
    )

    owner = _login(
        client,
        "owner@example.com",
    )

    other = _login(
        client,
        "other@example.com",
    )

    _generate_key(
        client,
        owner["access_token"],
    )

    upload = client.post(
        "/api/v1/files/upload",
        headers=_auth("owner@example.com", owner["access_token"]),
        files={
            "upload": (
                "secret.txt",
                b"owner plaintext",
                "text/plain",
            ),
        },
    )

    assert upload.status_code in (200, 201)

    file_id = upload.json()["id"]

    steal = client.get(
        f"/api/v1/files/{file_id}",
        headers=_auth("other@example.com", other["access_token"]),
    )

    assert steal.status_code == 404

    delete = client.delete(
        f"/api/v1/files/{file_id}",
        headers=_auth("other@example.com", other["access_token"]),
    )

    assert delete.status_code == 404

    owner_still_sees = client.get(
        f"/api/v1/files/{file_id}",
        headers=_auth("owner@example.com", owner["access_token"]),
    )

    assert owner_still_sees.status_code == 200


def test_cross_user_folder_restore_denied(
    client,
):

    _register(
        client,
        "folderowner@example.com",
        "folderowner",
    )

    _register(
        client,
        "folderother@example.com",
        "folderother",
    )

    owner = _login(
        client,
        "folderowner@example.com",
    )

    other = _login(
        client,
        "folderother@example.com",
    )

    _generate_key(
        client,
        owner["access_token"],
        name="folderowner-key",
    )

    import io
    import zipfile

    buffer = io.BytesIO()

    with zipfile.ZipFile(
        buffer,
        "w",
        zipfile.ZIP_DEFLATED,
    ) as archive:
        archive.writestr("nested/note.txt", "folder plaintext")

    upload = client.post(
        "/api/v1/folders/upload",
        headers=_auth(
            "folderowner@example.com",
            owner["access_token"],
        ),
        files={
            "upload": (
                "folder.zip",
                buffer.getvalue(),
                "application/zip",
            ),
        },
    )

    assert upload.status_code in (200, 201)

    folder_id = upload.json()["file_id"]

    restore = client.post(
        f"/api/v1/folders/{folder_id}/restore",
        headers=_auth(
            "folderother@example.com",
            other["access_token"],
        ),
    )

    assert restore.status_code == 404


def test_cross_user_key_operations_denied(
    client,
):

    _register(
        client,
        "keyowner@example.com",
        "keyowner",
    )

    _register(
        client,
        "keyother@example.com",
        "keyother",
    )

    owner = _login(
        client,
        "keyowner@example.com",
    )

    other = _login(
        client,
        "keyother@example.com",
    )

    generated = client.post(
        "/api/v1/keys",
        headers=_auth(
            "keyowner@example.com",
            owner["access_token"],
        ),
        json={
            "name": "owner-key",
            "validity_days": 365,
        },
    )

    assert generated.status_code == 201

    key_id = generated.json()["id"]

    revoke = client.post(
        f"/api/v1/keys/{key_id}/revoke",
        headers=_auth(
            "keyother@example.com",
            other["access_token"],
        ),
    )

    assert revoke.status_code == 404

    rotate = client.post(
        "/api/v1/keys/rotate",
        headers=_auth(
            "keyother@example.com",
            other["access_token"],
        ),
        json={
            "current_key_id": str(key_id),
        },
    )

    assert rotate.status_code == 404


# -------------------------------------------------
# 8.7 Key lifecycle
# -------------------------------------------------

def test_expired_key_rejected_for_encryption(
    client,
    db_session,
):

    _register(
        client,
        "expiredkey@example.com",
        "expiredkey",
    )

    token = _login(
        client,
        "expiredkey@example.com",
    )["access_token"]

    generated = client.post(
        "/api/v1/keys",
        headers=_auth(
            "expiredkey@example.com",
            token,
        ),
        json={
            "name": "short-lived",
            "validity_days": 1,
        },
    )

    assert generated.status_code == 201

    from datetime import UTC, datetime

    from app.domain.models.crypto_key import CryptoKey

    key = (
        db_session.query(CryptoKey)
        .filter(
            CryptoKey.name == "short-lived"
        )
        .first()
    )

    key.expires_at = datetime.now(UTC) - timedelta(
        hours=1
    )

    db_session.commit()

    encrypted = client.post(
        "/api/v1/encryption/text/encrypt",
        headers=_auth(
            "expiredkey@example.com",
            token,
        ),
        json={
            "plaintext": "should not encrypt",
        },
    )

    assert encrypted.status_code == 400


def test_key_rotation_promotes_new_key(
    client,
):

    _register(
        client,
        "keyrotation@example.com",
        "keyrotation",
    )

    token = _login(
        client,
        "keyrotation@example.com",
    )["access_token"]

    headers = _auth(
        "keyrotation@example.com",
        token,
    )

    first = client.post(
        "/api/v1/keys",
        headers=headers,
        json={
            "name": "generation-1",
            "validity_days": 365,
        },
    )

    assert first.status_code == 201

    first_id = first.json()["id"]

    rotated = client.post(
        "/api/v1/keys/rotate",
        headers=headers,
        json={
            "current_key_id": str(first_id),
        },
    )

    assert rotated.status_code == 200

    listing = client.get(
        "/api/v1/keys",
        headers=headers,
    )

    assert listing.status_code == 200

    by_id = {
        item["id"]: item
        for item in listing.json()["items"]
    }

    assert by_id[str(first_id)]["status"] == "revoked"

    assert (
        by_id[rotated.json()["new_key"]["id"]]["status"]
        == "active"
    )

    # Old container decryption still works with the
    # retired key, proving rotation does not lock out
    # previously encrypted data.
    encrypted = client.post(
        "/api/v1/encryption/text/encrypt",
        headers=headers,
        json={
            "plaintext": "pre-rotation secret",
        },
    )

    assert encrypted.status_code == 200

    decrypted = client.post(
        "/api/v1/encryption/text/decrypt",
        headers=headers,
        json=encrypted.json(),
    )

    assert decrypted.status_code == 200

    assert (
        decrypted.json()["plaintext"]
        == "pre-rotation secret"
    )


# -------------------------------------------------
# 8.4 Text encryption with AAD
# -------------------------------------------------

def test_text_encrypt_decrypt_with_aad(client):

    _register(
        client,
        "aad@example.com",
        "aaduser",
    )

    token = _login(
        client,
        "aad@example.com",
    )["access_token"]

    _generate_key(
        client,
        token,
        name="aad-key",
    )

    headers = _auth("aad@example.com", token)

    encrypted = client.post(
        "/api/v1/encryption/text/encrypt",
        headers=headers,
        json={
            "plaintext": "context-bound secret",
            "aad": "domain:payroll",
        },
    )

    assert encrypted.status_code == 200

    decrypted = client.post(
        "/api/v1/encryption/text/decrypt",
        headers=headers,
        json={
            **encrypted.json(),
            "aad": "domain:payroll",
        },
    )

    assert decrypted.status_code == 200

    assert (
        decrypted.json()["plaintext"]
        == "context-bound secret"
    )

    # The same ciphertext without the AAD must fail.
    missing = client.post(
        "/api/v1/encryption/text/decrypt",
        headers=headers,
        json=encrypted.json(),
    )

    assert missing.status_code == 422

    # A different AAD must fail.
    wrong = client.post(
        "/api/v1/encryption/text/decrypt",
        headers=headers,
        json={
            **encrypted.json(),
            "aad": "domain:finance",
        },
    )

    assert wrong.status_code == 422


def test_text_encrypt_rejects_oversized_plaintext(client):

    _register(
        client,
        "bigtext@example.com",
        "bigtext",
    )

    token = _login(
        client,
        "bigtext@example.com",
    )["access_token"]

    _generate_key(
        client,
        token,
        name="bigtext-key",
    )

    response = client.post(
        "/api/v1/encryption/text/encrypt",
        headers=_auth("bigtext@example.com", token),
        json={
            "plaintext": "A" * (1024 * 1024 + 1),
        },
    )

    assert response.status_code == 422
