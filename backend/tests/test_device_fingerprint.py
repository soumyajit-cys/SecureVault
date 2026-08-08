import pytest

from app.services.auth.device_fingerprint import (
    device_name,
    fingerprint_from_headers,
    parse_device,
)


UA_CHROME = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/126.0.0.0 Safari/537.36"
)

UA_MOBILE = (
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) "
    "Version/17.5 Mobile/15E148 Safari/604.1"
)


class TestFingerprint:
    def test_deterministic_for_same_headers(self):
        first = fingerprint_from_headers(UA_CHROME)
        second = fingerprint_from_headers(UA_CHROME)

        assert first == second
        assert len(first) == 64

    def test_different_agents_diverge(self):
        assert (
            fingerprint_from_headers(UA_CHROME)
            != fingerprint_from_headers(UA_MOBILE)
        )

    def test_header_set_matters(self):
        """
        Adding Accept-Language changes the fingerprint:
        a browser is only "the same device" when the
        full header signature matches.
        """

        plain = fingerprint_from_headers(UA_CHROME)

        with_lang = fingerprint_from_headers(
            UA_CHROME,
            accept_language="en-US,en;q=0.9",
        )

        assert plain != with_lang

    def test_no_headers_returns_none(self):
        assert fingerprint_from_headers(None) is None

        assert (
            fingerprint_from_headers(None, None, None)
            is None
        )


class TestParseDevice:
    def test_desktop_chrome(self):
        parsed = parse_device(UA_CHROME)

        assert parsed["device_type"] == "desktop"
        assert parsed["browser"] == "Chrome"
        assert parsed["os"] == "Windows 10"

    def test_mobile_iphone(self):
        parsed = parse_device(UA_MOBILE)

        assert parsed["device_type"] == "mobile"
        assert parsed["browser"] == "Safari"
        assert parsed["os"] == "iOS"

    def test_unknown_ua(self):
        assert parse_device(None) == {
            "device_type": "desktop",
            "os": "Unknown OS",
            "browser": "Unknown",
        }

    def test_device_name_label(self):
        assert (
            device_name(UA_CHROME)
            == "Chrome on Windows 10"
        )

        assert device_name(None) is None


# -------------------------------------------------
# Login integration: new-device flag
# -------------------------------------------------

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


def _login(
    client,
    email="finger@example.com",
    user_agent=UA_CHROME,
):
    return client.post(
        "/api/v1/auth/login",
        json={
            "email": email,
            "password": "CorrectHorseBatteryStaple!2026",
        },
        headers={
            "User-Agent": user_agent
        },
    )


def test_first_login_not_a_new_device(client):
    """
    The very first session a user creates is not
    flagged: there is no prior device to compare.
    """

    client.post(
        "/api/v1/auth/register",
        json={
            "email": "finger@example.com",
            "username": "finger",
            "password": "CorrectHorseBatteryStaple!2026",
        },
    )

    login = _login(client)

    assert login.status_code == 200

    assert login.json()["new_device"] is False


def test_same_device_login_not_new(client):
    """
    Logging in again from the same UA is the same
    device.
    """

    client.post(
        "/api/v1/auth/register",
        json={
            "email": "finger@example.com",
            "username": "finger",
            "password": "CorrectHorseBatteryStaple!2026",
        },
    )

    assert _login(client).json()["new_device"] is False

    second = _login(client)

    assert second.status_code == 200

    assert second.json()["new_device"] is False


def test_unknown_device_is_flagged(client, db_session):
    """
    A login from a different UA (while another
    session exists) is a new device, and the audit
    trail records device.new.
    """

    client.post(
        "/api/v1/auth/register",
        json={
            "email": "finger@example.com",
            "username": "finger",
            "password": "CorrectHorseBatteryStaple!2026",
        },
    )

    assert _login(client).json()["new_device"] is False

    login = _login(
        client,
        user_agent=UA_MOBILE,
    )

    assert login.status_code == 200

    assert login.json()["new_device"] is True

    from app.domain.models.audit_log import AuditLog

    events = [
        event.event
        for event in db_session.query(
            AuditLog
        ).all()
    ]

    assert "device.new" in events
