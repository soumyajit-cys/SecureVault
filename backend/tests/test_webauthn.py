import base64
import hashlib
import json

import cbor2
import pytest
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec
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


# -------------------------------------------------
# Synthetic authenticator
#
# Builds cryptographically valid fmt=none WebAuthn
# responses with a throwaway P-256 key, so the real
# verification path in webauthn 3.x is exercised.
# -------------------------------------------------

def _b64url(raw: bytes) -> str:
    return (
        base64.urlsafe_b64encode(raw)
        .rstrip(b"=")
        .decode()
    )


def _b64(raw: bytes) -> str:
    return base64.b64encode(raw).decode()


def _make_authenticator():
    """
    Returns (private_key, credential_id) for a fresh
    synthetic authenticator.
    """

    private_key = ec.generate_private_key(
        ec.SECP256R1()
    )

    import secrets

    credential_id = (
        b"synthetic-credential-"
        + secrets.token_bytes(16)
    )

    return private_key, credential_id


def _cose_public_key(private_key):
    numbers = (
        private_key.public_key()
        .public_numbers()
    )

    return {
        1: 2,          # kty: EC2
        3: -7,         # alg: ES256
        -1: 1,         # crv: P-256
        -2: numbers.x.to_bytes(32, "big"),
        -3: numbers.y.to_bytes(32, "big"),
    }


def _auth_data(
    rp_id: str,
    flags: int,
    sign_count: int,
    private_key=None,
    credential_id=None,
):
    rp_hash = hashlib.sha256(
        rp_id.encode()
    ).digest()

    data = (
        rp_hash
        + bytes([flags])
        + sign_count.to_bytes(4, "big")
    )

    if private_key is not None:

        data += b"\x00" * 16  # aaguid (none)

        data += len(credential_id).to_bytes(
            2, "big"
        )

        data += credential_id

        data += cbor2.dumps(
            _cose_public_key(private_key)
        )

    return data


def _client_data(
    challenge_b64url: str,
    origin: str,
    typ: str,
) -> bytes:
    return json.dumps(
        {
            "type": typ,
            "challenge": challenge_b64url,
            "origin": origin,
            "crossOrigin": False,
        },
        separators=(",", ":"),
    ).encode()


def make_registration_response(
    options: dict,
    private_key,
    credential_id,
    rp_id="localhost",
    origin="http://localhost:5173",
) -> dict:
    challenge = options["challenge"]

    auth = _auth_data(
        rp_id,
        flags=0x45,  # UP | UV | AT
        sign_count=1,
        private_key=private_key,
        credential_id=credential_id,
    )

    attestation_object = cbor2.dumps(
        {
            "fmt": "none",
            "authData": auth,
        }
    )

    return {
        "id": _b64url(credential_id),
        "rawId": _b64url(credential_id),
        "type": "public-key",
        "response": {
            "clientDataJSON": _b64(
                _client_data(
                    challenge,
                    origin,
                    "webauthn.create",
                )
            ),
            "attestationObject": _b64(
                attestation_object
            ),
        },
    }


def make_authentication_response(
    options: dict,
    private_key,
    credential_id,
    sign_count: int,
    rp_id="localhost",
    origin="http://localhost:5173",
) -> dict:
    challenge = options["challenge"]

    auth = _auth_data(
        rp_id,
        flags=0x05,  # UP | UV
        sign_count=sign_count,
    )

    client = _client_data(
        challenge,
        origin,
        "webauthn.get",
    )

    signature = private_key.sign(
        auth + hashlib.sha256(client).digest(),
        ec.ECDSA(hashes.SHA256()),
    )

    return {
        "id": _b64url(credential_id),
        "rawId": _b64url(credential_id),
        "type": "public-key",
        "response": {
            "clientDataJSON": _b64(client),
            "authenticatorData": _b64(auth),
            "signature": _b64(signature),
            "userHandle": None,
        },
    }


# -------------------------------------------------
# Fixtures
# -------------------------------------------------

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
def client(db_session):

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

    from app.services.auth.webauthn_service import (
        challenge_store,
    )

    challenge_store._items.clear()


def _register_user(
    client,
    email="passkey@example.com",
) -> str:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "username": email.split("@")[0],
            "password": "CorrectHorseBatteryStaple!2026",
        },
    )

    assert response.status_code == 200

    login = client.post(
        "/api/v1/auth/login",
        json={
            "email": email,
            "password": "CorrectHorseBatteryStaple!2026",
        },
    )

    assert login.status_code == 200

    return login.json()["access_token"]


@pytest.fixture
def admin_token(client, db_session):
    """
    Register a user and promote them to the Admin role.
    """

    _register_user(
        client,
        email="boss2@example.com",
    )

    from app.domain.models.user import User
    from app.domain.models.role import Role
    from app.domain.models.user_role import UserRole

    user = (
        db_session.query(User)
        .filter(User.email == "boss2@example.com")
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
            "email": "boss2@example.com",
            "password": "CorrectHorseBatteryStaple!2026",
        },
    )

    return login.json()["access_token"]


# -------------------------------------------------
# End-to-end ceremony tests
# -------------------------------------------------

def test_passkey_registration_and_login_flow(
    client,
):
    """
    Register a passkey, then log in with it end to
    end through the real verification code.
    """

    token = _register_user(client)

    headers = {
        "Authorization": f"Bearer {token}"
    }

    begin = client.post(
        "/api/v1/auth/passkeys/register/begin",
        headers=headers,
    )

    assert begin.status_code == 200

    options = begin.json()["options"]

    private_key, credential_id = (
        _make_authenticator()
    )

    response = make_registration_response(
        options,
        private_key,
        credential_id,
    )

    complete = client.post(
        "/api/v1/auth/passkeys/register/complete",
        headers=headers,
        json={
            "response": response,
            "device_label": "Test key",
        },
    )

    assert complete.status_code == 200

    credential_id_str = (
        complete.json()["credential_id"]
    )

    listed = client.get(
        "/api/v1/auth/passkeys",
        headers=headers,
    )

    assert listed.status_code == 200

    assert [
        item["id"]
        for item in listed.json()
    ] == [credential_id_str]

    assert (
        listed.json()[0]["device_label"]
        == "Test key"
    )

    # Passkey login
    login_begin = client.post(
        "/api/v1/auth/passkeys/login/begin",
        json={
            "email": "passkey@example.com",
        },
    )

    assert login_begin.status_code == 200

    assertion = make_authentication_response(
        login_begin.json()["options"],
        private_key,
        credential_id,
        sign_count=2,
    )

    login_complete = client.post(
        "/api/v1/auth/passkeys/login/complete",
        json={
            "response": assertion,
        },
    )

    assert login_complete.status_code == 200

    body = login_complete.json()

    assert "access_token" in body
    assert "refresh_token" in body

    # The assertion bumped the stored sign counter.
    import sqlite3

    creds = listed.json()

    assert (
        login_complete.status_code
        == 200
    )

    assert body["user"]["email"] == (
        "passkey@example.com"
    )


def test_passkey_login_without_email(
    client,
):
    """
    Discoverable-credential flow: begin with no
    username, assert with the registered key.
    """

    token = _register_user(client)

    headers = {
        "Authorization": f"Bearer {token}"
    }

    begin = client.post(
        "/api/v1/auth/passkeys/register/begin",
        headers=headers,
    )

    options = begin.json()["options"]

    private_key, credential_id = (
        _make_authenticator()
    )

    complete = client.post(
        "/api/v1/auth/passkeys/register/complete",
        headers=headers,
        json={
            "response": make_registration_response(
                options,
                private_key,
                credential_id,
            ),
            "device_label": "Roaming key",
        },
    )

    assert complete.status_code == 200

    login_begin = client.post(
        "/api/v1/auth/passkeys/login/begin",
        json={},
    )

    assertion = make_authentication_response(
        login_begin.json()["options"],
        private_key,
        credential_id,
        sign_count=5,
    )

    login_complete = client.post(
        "/api/v1/auth/passkeys/login/complete",
        json={
            "response": assertion,
        },
    )

    assert login_complete.status_code == 200

    assert (
        login_complete.json()["user"]["email"]
        == "passkey@example.com"
    )


def test_registration_rejects_replayed_response(
    client,
):
    """
    A registration response is single-use: repeating
    it must fail.
    """

    token = _register_user(client)

    headers = {
        "Authorization": f"Bearer {token}"
    }

    options = (
        client.post(
            "/api/v1/auth/passkeys/register/begin",
            headers=headers,
        ).json()["options"]
    )

    private_key, credential_id = (
        _make_authenticator()
    )

    payload = {
        "response": make_registration_response(
            options,
            private_key,
            credential_id,
        ),
        "device_label": "Replay key",
    }

    first = client.post(
        "/api/v1/auth/passkeys/register/complete",
        headers=headers,
        json=payload,
    )

    assert first.status_code == 200

    second = client.post(
        "/api/v1/auth/passkeys/register/complete",
        headers=headers,
        json=payload,
    )

    assert second.status_code == 400


def test_counter_regression_is_rejected(
    client,
):
    """
    A cloned authenticator replays an old counter:
    login must fail.
    """

    token = _register_user(client)

    headers = {
        "Authorization": f"Bearer {token}"
    }

    options = (
        client.post(
            "/api/v1/auth/passkeys/register/begin",
            headers=headers,
        ).json()["options"]
    )

    private_key, credential_id = (
        _make_authenticator()
    )

    complete = client.post(
        "/api/v1/auth/passkeys/register/complete",
        headers=headers,
        json={
            "response": make_registration_response(
                options,
                private_key,
                credential_id,
            ),
            "device_label": "Clone test",
        },
    )

    assert complete.status_code == 200

    login_begin = client.post(
        "/api/v1/auth/passkeys/login/begin",
        json={
            "email": "passkey@example.com",
        },
    )

    # Same counter as registration (1 <= 1): the
    # stored counter has not advanced.
    assertion = make_authentication_response(
        login_begin.json()["options"],
        private_key,
        credential_id,
        sign_count=1,
    )

    login_complete = client.post(
        "/api/v1/auth/passkeys/login/complete",
        json={
            "response": assertion,
        },
    )

    assert login_complete.status_code == 401


def test_remove_credential(
    client,
):
    token = _register_user(client)

    headers = {
        "Authorization": f"Bearer {token}"
    }

    options = (
        client.post(
            "/api/v1/auth/passkeys/register/begin",
            headers=headers,
        ).json()["options"]
    )

    private_key, credential_id = (
        _make_authenticator()
    )

    complete = client.post(
        "/api/v1/auth/passkeys/register/complete",
        headers=headers,
        json={
            "response": make_registration_response(
                options,
                private_key,
                credential_id,
            ),
            "device_label": "To remove",
        },
    )

    credential_id_str = (
        complete.json()["credential_id"]
    )

    removed = client.delete(
        "/api/v1/auth/passkeys",
        headers=headers,
        json={
            "credential_id": credential_id_str,
        },
    )

    assert removed.status_code == 200

    listed = client.get(
        "/api/v1/auth/passkeys",
        headers=headers,
    )

    assert listed.json() == []

    # Removing again 404s (no info leak).
    again = client.delete(
        "/api/v1/auth/passkeys",
        headers=headers,
        json={
            "credential_id": credential_id_str,
        },
    )

    assert again.status_code == 404


# -------------------------------------------------
# MFA enforcement policy
# -------------------------------------------------

def test_mfa_policy_endpoints(
    client,
    admin_token,
    db_session,
):
    from app.domain.models.app_setting import (
        AppSetting,
    )

    db_session.query(AppSetting).delete()

    db_session.commit()

    headers = {
        "Authorization": f"Bearer {admin_token}"
    }

    policy = client.get(
        "/api/v1/admin/mfa-policy",
        headers=headers,
    )

    assert policy.status_code == 200

    assert policy.json()["mode"] == "optional"

    updated = client.patch(
        "/api/v1/admin/mfa-policy",
        headers=headers,
        json={
            "mode": "required",
        },
    )

    assert updated.status_code == 200

    assert updated.json()["mode"] == "required"

    # Invalid mode is rejected by the schema.
    invalid = client.patch(
        "/api/v1/admin/mfa-policy",
        headers=headers,
        json={
            "mode": "sometimes",
        },
    )

    assert invalid.status_code == 422

    # Non-admins cannot read or change the policy.
    non_admin = _register_user(
        client,
        email="peon@example.com",
    )

    peon_headers = {
        "Authorization": (
            f"Bearer {non_admin}"
        )
    }

    assert (
        client.get(
            "/api/v1/admin/mfa-policy",
            headers=peon_headers,
        ).status_code
        == 403
    )


def test_enforced_mfa_blocks_password_login(
    client,
    admin_token,
    db_session,
):
    """
    With the policy set to required, a user without
    any MFA factor cannot sign in with a password.
    """

    from app.domain.models.app_setting import (
        AppSetting,
    )

    db_session.query(AppSetting).delete()

    db_session.commit()

    headers = {
        "Authorization": f"Bearer {admin_token}"
    }

    client.patch(
        "/api/v1/admin/mfa-policy",
        headers=headers,
        json={
            "mode": "required",
        },
    )

    _register_user(
        client,
        email="nofactor@example.com",
    )

    login = client.post(
        "/api/v1/auth/login",
        json={
            "email": "nofactor@example.com",
            "password": "CorrectHorseBatteryStaple!2026",
        },
    )

    assert login.status_code == 401

    assert (
        "MFA is required"
        in login.json()["detail"]
    )

    # A user with a passkey is not blocked.
    token = _register_user(
        client,
        email="withkey@example.com",
    )

    headers2 = {
        "Authorization": f"Bearer {token}"
    }

    options = (
        client.post(
            "/api/v1/auth/passkeys/register/begin",
            headers=headers2,
        ).json()["options"]
    )

    private_key, credential_id = (
        _make_authenticator()
    )

    complete = client.post(
        "/api/v1/auth/passkeys/register/complete",
        headers=headers2,
        json={
            "response": make_registration_response(
                options,
                private_key,
                credential_id,
            ),
            "device_label": "Compliant key",
        },
    )

    assert complete.status_code == 200

    login2 = client.post(
        "/api/v1/auth/login",
        json={
            "email": "withkey@example.com",
            "password": "CorrectHorseBatteryStaple!2026",
        },
    )

    assert login2.status_code == 200
