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


@pytest.fixture
def registered(client):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "cors@example.com",
            "username": "corsuser",
            "password": "SecureVault#2026",
        },
    )

    assert response.status_code in (200, 201)


def login(client):
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "cors@example.com",
            "password": "SecureVault#2026",
        },
    )

    assert response.status_code == 200

    return response


def test_login_body_carries_csrf_token(client, registered):
    """The JSON body mirrors the readable CSRF cookie so a
    cross-origin client (no document.cookie access to backend
    cookies) can still do double-submit from memory."""

    body = login(client).json()

    assert body["csrf_token"]
    assert body["csrf_token"] == client.cookies.get("sv_csrf")


def test_refresh_with_body_token_as_header(client, registered):
    """Simulates the cross-origin client: header taken from the
    JSON body, cookies attached by the browser."""

    body_token = login(client).json()["csrf_token"]

    refresh = client.post(
        "/api/v1/auth/refresh",
        json={},
        headers={"X-CSRF-Token": body_token},
    )

    assert refresh.status_code == 200
    assert refresh.json()["csrf_token"]
    assert refresh.json()["csrf_token"] == client.cookies.get("sv_csrf")


def test_csrf_bootstrap_endpoint(client, registered):
    login(client)

    echoed = client.get("/api/v1/auth/csrf")

    assert echoed.status_code == 200
    assert echoed.json()["csrf_token"] == client.cookies.get("sv_csrf")

    client.cookies.clear()

    assert client.get("/api/v1/auth/csrf").status_code == 401


def test_auth_cookies_default_samesite_strict(client, registered):
    fresh = login(client)
    raw = fresh.headers.get_list("set-cookie")
    assert raw, "expected Set-Cookie headers on login"
    assert any("samesite=strict" in c.lower() for c in raw)
    assert any("httponly" in c.lower() for c in raw)


def test_cookie_samesite_config(monkeypatch):
    import app.core.cookie_auth as cookies

    monkeypatch.setattr(cookies.get_settings(), "APP_ENV", "development")
    monkeypatch.setattr(
        cookies.get_settings(), "COOKIE_SAMESITE", "strict"
    )
    assert cookies._cookie_samesite() == "strict"

    monkeypatch.setattr(
        cookies.get_settings(), "COOKIE_SAMESITE", "lax"
    )
    assert cookies._cookie_samesite() == "lax"

    monkeypatch.setattr(
        cookies.get_settings(), "COOKIE_SAMESITE", "bogus"
    )
    with pytest.raises(RuntimeError):
        cookies._cookie_samesite()

    # Production forces none regardless of the setting.
    monkeypatch.setattr(cookies.get_settings(), "APP_ENV", "production")
    monkeypatch.setattr(
        cookies.get_settings(), "COOKIE_SAMESITE", "strict"
    )
    assert cookies._cookie_samesite() == "none"
