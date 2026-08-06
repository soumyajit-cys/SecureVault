import pyotp
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

NEW_PASSWORD = "NewSecureVault#2027"


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


def _token(
    client,
    email: str,
    username: str,
    password: str = PASSWORD,
) -> str:

    _register(client, email, username, password)

    return _login(client, email, password)[
        "access_token"
    ]


def _make_admin(
    client,
    db_session,
    email: str = "boss@example.com",
    username: str = "boss",
) -> str:

    _register(client, email, username)

    from app.domain.models.user import User
    from app.domain.models.role import Role
    from app.domain.models.user_role import UserRole

    user = (
        db_session.query(User)
        .filter(User.email == email)
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

    return _login(client, email)[
        "access_token"
    ]


def _enable_mfa(
    client,
    token: str,
) -> dict:
    """
    Full MFA enablement; returns the recovery codes.
    """

    headers = {
        "Authorization": f"Bearer {token}"
    }

    setup = client.post(
        "/api/v1/auth/mfa/setup",
        headers=headers,
    )

    assert setup.status_code == 200

    secret = setup.json()["secret"]

    code = pyotp.TOTP(secret).now()

    enabled = client.post(
        "/api/v1/auth/mfa/enable",
        headers=headers,
        json={
            "secret": secret,
            "code": code,
        },
    )

    assert enabled.status_code == 200

    return enabled.json()


# -------------------------------------------------
# MFA
# -------------------------------------------------

def test_mfa_setup_requires_authentication(client):

    status = client.get(
        "/api/v1/auth/mfa/status"
    )

    assert status.status_code == 401


def test_mfa_enable_rejects_bad_code(client):

    token = _token(
        client,
        "mfa@example.com",
        "mfauser",
    )

    headers = {
        "Authorization": f"Bearer {token}"
    }

    setup = client.post(
        "/api/v1/auth/mfa/setup",
        headers=headers,
    )

    secret = setup.json()["secret"]

    bad = client.post(
        "/api/v1/auth/mfa/enable",
        headers=headers,
        json={
            "secret": secret,
            "code": "000000",
        },
    )

    assert bad.status_code == 401

    status = client.get(
        "/api/v1/auth/mfa/status",
        headers=headers,
    )

    assert status.json()["enabled"] is False


def test_mfa_login_flow_with_totp(client):

    token = _token(
        client,
        "mfa2@example.com",
        "mfa2user",
    )

    result = _enable_mfa(client, token)

    assert len(result["recovery_codes"]) == 10

    login = client.post(
        "/api/v1/auth/login",
        json={
            "email": "mfa2@example.com",
            "password": PASSWORD,
        },
    )

    assert login.status_code == 200

    body = login.json()

    assert body["mfa_required"] is True

    assert "mfa_token" in body

    assert "access_token" not in body

    # Second setup attempt is rejected while enabled.
    setup = client.post(
        "/api/v1/auth/mfa/setup",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert setup.status_code == 409

    # Verify with a recovery code.
    recovery = client.post(
        "/api/v1/auth/mfa/verify",
        json={
            "mfa_token": body["mfa_token"],
            "code": result["recovery_codes"][0],
        },
    )

    assert recovery.status_code == 200

    assert "access_token" in recovery.json()


def test_mfa_totp_verification(client):

    token = _token(
        client,
        "mfa3@example.com",
        "mfa3user",
    )

    _enable_mfa(client, token)

    login = client.post(
        "/api/v1/auth/login",
        json={
            "email": "mfa3@example.com",
            "password": PASSWORD,
        },
    )

    mfa_token = login.json()["mfa_token"]

    wrong = client.post(
        "/api/v1/auth/mfa/verify",
        json={
            "mfa_token": mfa_token,
            "code": "000000",
        },
    )

    assert wrong.status_code == 401


def test_mfa_recovery_code_single_use(client, db_session):

    token = _token(
        client,
        "mfa4@example.com",
        "mfa4user",
    )

    result = _enable_mfa(client, token)

    from app.domain.models.user import User

    user = (
        db_session.query(User)
        .filter(
            User.email == "mfa4@example.com"
        )
        .first()
    )

    assert user.totp_secret is not None

    # Login with a real TOTP code derived from the
    # stored secret.
    code = pyotp.TOTP(
        user.totp_secret
    ).now()

    login = client.post(
        "/api/v1/auth/login",
        json={
            "email": "mfa4@example.com",
            "password": PASSWORD,
        },
    )

    assert login.json()["mfa_required"] is True

    verified = client.post(
        "/api/v1/auth/mfa/verify",
        json={
            "mfa_token": login.json()["mfa_token"],
            "code": code,
        },
    )

    assert verified.status_code == 200

    assert "access_token" in verified.json()

    # Recovery codes are single-use.
    first = client.post(
        "/api/v1/auth/login",
        json={
            "email": "mfa4@example.com",
            "password": PASSWORD,
        },
    )

    used_code = client.post(
        "/api/v1/auth/mfa/verify",
        json={
            "mfa_token": first.json()["mfa_token"],
            "code": result["recovery_codes"][1],
        },
    )

    assert used_code.status_code == 200

    second = client.post(
        "/api/v1/auth/login",
        json={
            "email": "mfa4@example.com",
            "password": PASSWORD,
        },
    )

    replay = client.post(
        "/api/v1/auth/mfa/verify",
        json={
            "mfa_token": second.json()["mfa_token"],
            "code": result["recovery_codes"][1],
        },
    )

    assert replay.status_code == 401


def test_mfa_disable(client, db_session):

    token = _token(
        client,
        "mfa5@example.com",
        "mfa5user",
    )

    result = _enable_mfa(client, token)

    from app.domain.models.user import User

    user = (
        db_session.query(User)
        .filter(
            User.email == "mfa5@example.com"
        )
        .first()
    )

    headers = {
        "Authorization": f"Bearer {token}"
    }

    disabled = client.post(
        "/api/v1/auth/mfa/disable",
        headers=headers,
        json={
            "code": result["recovery_codes"][0],
        },
    )

    assert disabled.status_code == 200

    status = client.get(
        "/api/v1/auth/mfa/status",
        headers=headers,
    )

    assert status.json()["enabled"] is False

    login = client.post(
        "/api/v1/auth/login",
        json={
            "email": "mfa5@example.com",
            "password": PASSWORD,
        },
    )

    assert login.status_code == 200

    assert "access_token" in login.json()

    assert user.totp_secret is None


# -------------------------------------------------
# Password reset
# -------------------------------------------------

def test_password_reset_flow(client):

    _register(
        client,
        "reset@example.com",
        "resetuser",
    )

    requested = client.post(
        "/api/v1/auth/password-reset/request",
        json={
            "email": "reset@example.com",
        },
    )

    assert requested.status_code == 200

    assert requested.json()["message"]

    bad = client.post(
        "/api/v1/auth/password-reset/confirm",
        json={
            "token": "bogus-token",
            "new_password": NEW_PASSWORD,
        },
    )

    assert bad.status_code in (400, 401)


def test_password_reset_with_valid_token(
    client,
    db_session,
):

    _register(
        client,
        "reset2@example.com",
        "reset2user",
    )

    client.post(
        "/api/v1/auth/password-reset/request",
        json={
            "email": "reset2@example.com",
        },
    )

    import hashlib

    from app.domain.models.password_reset_token import (
        PasswordResetToken,
    )

    # Reconstruct the raw token by brute-forcing the
    # digest is impossible; instead capture the token
    # by monkeypatching the email service.
    captured: dict = {}

    from app.services.auth.email_service import (
        EmailService,
    )

    original_send = EmailService.send

    def fake_send(self, to, subject, body):
        captured["to"] = to
        captured["body"] = body
        return True

    EmailService.send = fake_send

    try:
        client.post(
            "/api/v1/auth/password-reset/request",
            json={
                "email": "reset2@example.com",
            },
        )
    finally:
        EmailService.send = original_send

    import re

    match = re.search(
        r"token=([A-Za-z0-9_-]+)",
        captured["body"],
    )

    assert match, captured["body"]

    raw_token = match.group(1)

    weak = client.post(
        "/api/v1/auth/password-reset/confirm",
        json={
            "token": raw_token,
            "new_password": "short",
        },
    )

    assert weak.status_code in (400, 401, 422)

    reset = client.post(
        "/api/v1/auth/password-reset/confirm",
        json={
            "token": raw_token,
            "new_password": NEW_PASSWORD,
        },
    )

    assert reset.status_code == 200

    old_login = client.post(
        "/api/v1/auth/login",
        json={
            "email": "reset2@example.com",
            "password": PASSWORD,
        },
    )

    assert old_login.status_code == 401

    new_login = client.post(
        "/api/v1/auth/login",
        json={
            "email": "reset2@example.com",
            "password": NEW_PASSWORD,
        },
    )

    assert new_login.status_code == 200

    # Token is single-use.
    replay = client.post(
        "/api/v1/auth/password-reset/confirm",
        json={
            "token": raw_token,
            "new_password": PASSWORD,
        },
    )

    assert replay.status_code in (400, 401)


def test_password_reset_unknown_email_hides_existence(
    client,
):

    response = client.post(
        "/api/v1/auth/password-reset/request",
        json={
            "email": "ghost@example.com",
        },
    )

    assert response.status_code == 200

    assert "has been sent" in response.json()[
        "message"
    ]


def test_password_reset_revokes_sessions(
    client,
    db_session,
):

    token = _token(
        client,
        "reset3@example.com",
        "reset3user",
    )

    headers = {
        "Authorization": f"Bearer {token}"
    }

    sessions = client.get(
        "/api/v1/auth/sessions",
        headers=headers,
    )

    assert len(sessions.json()) == 1

    captured: dict = {}

    from app.services.auth.email_service import (
        EmailService,
    )

    original_send = EmailService.send

    def fake_send(self, to, subject, body):
        captured["body"] = body
        return True

    EmailService.send = fake_send

    try:
        client.post(
            "/api/v1/auth/password-reset/request",
            json={
                "email": "reset3@example.com",
            },
        )
    finally:
        EmailService.send = original_send

    import re

    raw_token = re.search(
        r"token=([A-Za-z0-9_-]+)",
        captured["body"],
    ).group(1)

    client.post(
        "/api/v1/auth/password-reset/confirm",
        json={
            "token": raw_token,
            "new_password": NEW_PASSWORD,
        },
    )

    # Old access token no longer maps to a live
    # session for refresh purposes; the session row
    # is revoked.
    from app.domain.models.session import Session
    from app.domain.models.user import User

    user = (
        db_session.query(User)
        .filter(
            User.email == "reset3@example.com"
        )
        .first()
    )

    sessions = (
        db_session.query(Session)
        .filter(
            Session.user_id == user.id
        )
        .all()
    )

    assert all(s.revoked for s in sessions)


# -------------------------------------------------
# Session management
# -------------------------------------------------

def test_session_list_and_revoke(client):

    token = _token(
        client,
        "sess@example.com",
        "sessuser",
    )

    headers = {
        "Authorization": f"Bearer {token}"
    }

    sessions = client.get(
        "/api/v1/auth/sessions",
        headers=headers,
    )

    assert sessions.status_code == 200

    assert len(sessions.json()) == 1

    assert "last_seen_at" in sessions.json()[0]

    second_token = _login(
        client,
        "sess@example.com",
    )["access_token"]

    sessions = client.get(
        "/api/v1/auth/sessions",
        headers=headers,
    )

    assert len(sessions.json()) == 2

    victim_id = next(
        s["id"]
        for s in sessions.json()
        if s["session_identifier"]
        != sessions.json()[0][
            "session_identifier"
        ]
    )

    revoked = client.delete(
        f"/api/v1/auth/sessions/{victim_id}",
        headers=headers,
    )

    assert revoked.status_code == 200

    remaining = client.get(
        "/api/v1/auth/sessions",
        headers=headers,
    )

    assert len(remaining.json()) == 1


def test_session_revoke_all_keeps_current(client):

    token = _token(
        client,
        "sess2@example.com",
        "sess2user",
    )

    headers = {
        "Authorization": f"Bearer {token}"
    }

    _login(client, "sess2@example.com")

    _login(client, "sess2@example.com")

    revoked = client.post(
        "/api/v1/auth/sessions/revoke-all",
        headers=headers,
    )

    assert revoked.status_code == 200

    sessions = client.get(
        "/api/v1/auth/sessions",
        headers=headers,
    )

    assert len(sessions.json()) == 1

    # The kept session still works.
    me = client.get(
        "/api/v1/profile/me",
        headers=headers,
    )

    assert me.status_code == 200


def test_revoke_unknown_session_404(client):

    token = _token(
        client,
        "sess3@example.com",
        "sess3user",
    )

    import uuid

    response = client.delete(
        f"/api/v1/auth/sessions/{uuid.uuid4()}",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 404


# -------------------------------------------------
# Admin user management
# -------------------------------------------------

def test_admin_create_update_roles_delete(
    client,
    db_session,
):

    admin = _make_admin(client, db_session)

    admin_headers = {
        "Authorization": f"Bearer {admin}"
    }

    created = client.post(
        "/api/v1/admin/users",
        headers=admin_headers,
        json={
            "email": "newbie@example.com",
            "username": "newbie",
            "password": PASSWORD,
            "roles": ["User"],
            "storage_quota_bytes": (
                1024 * 1024
            ),
        },
    )

    assert created.status_code == 201

    user_id = created.json()["id"]

    detail = client.get(
        f"/api/v1/admin/users/{user_id}",
        headers=admin_headers,
    )

    assert detail.status_code == 200

    assert (
        detail.json()["storage_quota_bytes"]
        == 1024 * 1024
    )

    patched = client.patch(
        f"/api/v1/admin/users/{user_id}",
        headers=admin_headers,
        json={
            "username": "newbie2",
            "storage_quota_bytes": 2 * 1024 * 1024,
        },
    )

    assert patched.status_code == 200

    assert patched.json()["username"] == "newbie2"

    roles = client.post(
        f"/api/v1/admin/users/{user_id}/roles",
        headers=admin_headers,
        json={
            "roles": ["Admin"],
        },
    )

    assert roles.status_code == 200

    role_names = {
        r["name"]
        for r in roles.json()["roles"]
    }

    assert "Admin" in role_names

    deleted = client.delete(
        f"/api/v1/admin/users/{user_id}",
        headers=admin_headers,
    )

    assert deleted.status_code == 200

    login = client.post(
        "/api/v1/auth/login",
        json={
            "email": "newbie@example.com",
            "password": PASSWORD,
        },
    )

    assert login.status_code == 401


def test_admin_cannot_delete_self(client, db_session):

    admin = _make_admin(
        client,
        db_session,
        email="boss2@example.com",
        username="boss2",
    )

    from app.domain.models.user import User

    user = (
        db_session.query(User)
        .filter(
            User.email == "boss2@example.com"
        )
        .first()
    )

    response = client.delete(
        f"/api/v1/admin/users/{user.id}",
        headers={
            "Authorization": f"Bearer {admin}"
        },
    )

    assert response.status_code == 400


def test_admin_create_requires_valid_password(
    client,
    db_session,
):

    admin = _make_admin(client, db_session)

    weak = client.post(
        "/api/v1/admin/users",
        headers={
            "Authorization": f"Bearer {admin}"
        },
        json={
            "email": "weak@example.com",
            "username": "weakuser",
            "password": "Passwordpassword1",
            "roles": [],
        },
    )

    assert weak.status_code in (400, 401)


# -------------------------------------------------
# Quota enforcement
# -------------------------------------------------

def test_upload_respects_quota(
    client,
    db_session,
):

    admin = _make_admin(client, db_session)

    admin_headers = {
        "Authorization": f"Bearer {admin}"
    }

    created = client.post(
        "/api/v1/admin/users",
        headers=admin_headers,
        json={
            "email": "quota@example.com",
            "username": "quotauser",
            "password": PASSWORD,
            "roles": ["User"],
            "storage_quota_bytes": 2048,
        },
    )

    assert created.status_code == 201

    user_token = _login(
        client,
        "quota@example.com",
    )["access_token"]

    headers = {
        "Authorization": f"Bearer {user_token}"
    }

    client.post(
        "/api/v1/keys",
        headers=headers,
        json={"name": "primary"},
    )

    quota = client.get(
        "/api/v1/profile/quota",
        headers=headers,
    )

    assert quota.status_code == 200

    assert (
        quota.json()["storage_quota_bytes"]
        == 2048
    )

    small = client.post(
        "/api/v1/files/upload",
        headers=headers,
        files={
            "upload": (
                "small.txt",
                b"x" * 512,
                "text/plain",
            )
        },
    )

    assert small.status_code == 201

    large = client.post(
        "/api/v1/files/upload",
        headers=headers,
        files={
            "upload": (
                "large.txt",
                b"x" * 4096,
                "text/plain",
            )
        },
    )

    assert large.status_code == 413

    usage = client.get(
        "/api/v1/profile/quota",
        headers=headers,
    )

    assert usage.json()["storage_usage_bytes"] > 0

    assert usage.json()["remaining_bytes"] >= 0


def test_unlimited_quota_allows_large_upload(
    client,
    db_session,
):

    token = _token(
        client,
        "free@example.com",
        "freeuser",
    )

    headers = {
        "Authorization": f"Bearer {token}"
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
                "big.bin",
                b"x" * 256 * 1024,
                "application/octet-stream",
            )
        },
    )

    assert upload.status_code == 201

    quota = client.get(
        "/api/v1/profile/quota",
        headers=headers,
    )

    assert quota.json()["storage_quota_bytes"] is None


# -------------------------------------------------
# Audit export
# -------------------------------------------------

def test_audit_csv_export(client, db_session):

    admin = _make_admin(client, db_session)

    response = client.get(
        "/api/v1/audit/admin/export",
        headers={
            "Authorization": f"Bearer {admin}"
        },
    )

    assert response.status_code == 200

    assert response.headers[
        "content-type"
    ].startswith("text/csv")

    assert (
        "attachment"
        in response.headers["content-disposition"]
    )

    text = response.text

    assert text.startswith("id,created_at")

    assert "user.registered" in text


def test_audit_export_requires_admin(
    client,
    db_session,
):

    token = _token(
        client,
        "peon@example.com",
        "peonuser",
    )

    response = client.get(
        "/api/v1/audit/admin/export",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 403


# -------------------------------------------------
# Login rate limiting & lockout
# -------------------------------------------------

def test_login_rate_limit_exceeded(client, db_session):

    _register(
        client,
        "ratelimit@example.com",
        "ratelimituser",
    )

    statuses = []

    for _ in range(12):

        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "ratelimit@example.com",
                "password": "wrong-password",
            },
        )

        statuses.append(
            response.status_code
        )

    assert 429 in statuses


def test_account_locks_after_max_attempts(
    client,
    db_session,
):

    _register(
        client,
        "lockme@example.com",
        "lockmeuser",
    )

    from app.core.config import get_settings

    attempts = get_settings().MAX_LOGIN_ATTEMPTS

    for _ in range(attempts):

        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "lockme@example.com",
                "password": "wrong-password",
            },
        )

        assert response.status_code == 401

    locked = client.post(
        "/api/v1/auth/login",
        json={
            "email": "lockme@example.com",
            "password": PASSWORD,
        },
    )

    assert locked.status_code in (401, 403)


# -------------------------------------------------
# Pwned password check
# -------------------------------------------------

def test_pwned_password_blocked_when_enabled(
    client,
    db_session,
    monkeypatch,
):

    from app.services.auth.pwned_service import (
        PwnedPasswordChecker,
    )

    class _FakePwned(PwnedPasswordChecker):

        def is_pwned(
            self,
            password: str,
        ) -> bool:
            return True

    monkeypatch.setattr(
        PwnedPasswordChecker,
        "is_pwned",
        _FakePwned.is_pwned,
    )

    import app.core.config as config_module

    settings = config_module.get_settings()

    original = settings.PWNED_CHECK_ENABLED

    settings.PWNED_CHECK_ENABLED = True

    try:

        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "pwned@example.com",
                "username": "pwneduser",
                "password": PASSWORD,
            },
        )

        assert response.status_code in (400, 401)

    finally:

        settings.PWNED_CHECK_ENABLED = (
            original
        )
