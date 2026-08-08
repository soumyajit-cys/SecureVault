import json

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

    from app.core.logging import configure_logging

    configure_logging()

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


def test_authenticated_request_logs_user_id(
    client,
    db_session,
    capsys,
):
    """
    The request-log middleware attaches the acting
    user_id to request_completed entries.
    """

    client.post(
        "/api/v1/auth/register",
        json={
            "email": "log@example.com",
            "username": "loguser",
            "password": "CorrectHorseBatteryStaple!2026",
        },
    )

    login = client.post(
        "/api/v1/auth/login",
        json={
            "email": "log@example.com",
            "password": "CorrectHorseBatteryStaple!2026",
        },
    )

    token = login.json()["access_token"]

    capsys.readouterr()  # clear earlier output

    response = client.get(
        "/api/v1/profile/me",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 200

    captured = capsys.readouterr().out

    user_id = (
        response.json()["id"]
        if "id" in response.json()
        else None
    )

    completed = [
        json.loads(line)
        for line in captured.splitlines()
        if "request_completed" in line
    ]

    assert completed

    entry = completed[0]

    assert entry["event"] == "request_completed"

    assert entry["user_id"] == user_id
