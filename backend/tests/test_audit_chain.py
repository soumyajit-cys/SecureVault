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
from app.services.audit_service import (
    AuditService,
)

from uuid import uuid4

from app.domain.models.audit_log import (
    AuditLog,
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


def _service(db_session):

    from app.infrastructure.repositories.audit_log_repository import (
        SQLAlchemyAuditLogRepository,
    )

    return AuditService(
        SQLAlchemyAuditLogRepository(db_session)
    )


def test_chain_is_consistent(db_session):

    service = _service(db_session)

    for i in range(5):
        service.log(
            uuid4(),
            f"event.{i}",
            details=f"payload-{i}",
        )

    assert service.verify_chain() == []


def test_chain_links_entries(db_session):

    service = _service(db_session)

    service.log(uuid4(), "event.a")
    service.log(uuid4(), "event.b")
    service.log(uuid4(), "event.c")

    entries = (
        db_session.query(AuditLog)
        .order_by(AuditLog.created_at.asc())
        .all()
    )

    first, second, third = entries

    assert second.prev_hash == first.entry_hash

    assert third.prev_hash == second.entry_hash


def test_tampering_is_detected(db_session):

    service = _service(db_session)

    service.log(uuid4(), "event.a")
    service.log(uuid4(), "event.b")

    entry = (
        db_session.query(AuditLog)
        .filter(
            AuditLog.action == "event.b"
        )
        .one()
    )

    entry.details = "altered by attacker"

    db_session.commit()

    issues = service.verify_chain()

    assert len(issues) == 1

    assert "entry_hash mismatch" in issues[0]


def test_forged_prev_hash_is_detected(db_session):

    service = _service(db_session)

    service.log(uuid4(), "event.a")
    service.log(uuid4(), "event.b")
    service.log(uuid4(), "event.c")

    third = (
        db_session.query(AuditLog)
        .filter(
            AuditLog.action == "event.c"
        )
        .one()
    )

    third.prev_hash = "deadbeef" * 8

    db_session.commit()

    issues = service.verify_chain()

    assert any(
        "prev_hash mismatch" in issue
        for issue in issues
    )


def test_verify_chain_endpoint(client, db_session):

    _service(db_session).log(uuid4(), "event.x")

    _register(
        client,
        "auditboss@example.com",
        "auditboss",
    )

    from app.domain.models.user import User
    from app.domain.models.role import Role
    from app.domain.models.user_role import UserRole

    user = (
        db_session.query(User)
        .filter(User.email == "auditboss@example.com")
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
            "email": "auditboss@example.com",
            "password": "CorrectHorseBatteryStaple!2026",
        },
    )

    headers = {
        "Authorization": (
            f"Bearer {login.json()['access_token']}"
        )
    }

    response = client.get(
        "/api/v1/admin/audit/verify-chain",
        headers=headers,
    )

    assert response.status_code == 200

    body = response.json()

    assert body["verified"] is True


def _register(client, email, username):

    return client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "username": username,
            "password": (
                "CorrectHorseBatteryStaple!2026"
            ),
        },
    )


def test_failed_login_is_audited(client, db_session):

    client.post(
        "/api/v1/auth/register",
        json={
            "email": "auditfail@example.com",
            "username": "auditfail",
            "password": "CorrectHorseBatteryStaple!2026",
        },
    )

    client.post(
        "/api/v1/auth/login",
        json={
            "email": "auditfail@example.com",
            "password": "WrongPassword!2026",
        },
    )

    failed = (
        db_session.query(AuditLog)
        .filter(
            AuditLog.action == "login.failed"
        )
        .all()
    )

    assert len(failed) == 1

    assert "ip=" in (failed[0].details or "")
