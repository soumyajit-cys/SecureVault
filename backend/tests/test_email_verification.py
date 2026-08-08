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
from app.services.auth.email_service import (
    EmailService,
)
from app.services.auth.email_verification_service import (
    EmailVerificationService,
)


class RecordingEmailService(EmailService):
    def __init__(self) -> None:
        super().__init__()
        self.sent = []

    def send(self, to, subject, body) -> bool:
        self.sent.append(
            {
                "to": to,
                "subject": subject,
                "body": body,
            }
        )
        return True


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
def client(db_session, monkeypatch):

    from app.core.config import get_settings

    from app.services.auth import (
        auth_service as auth_service_module,
    )

    from app.services.auth import (
        email_verification_service as evs_module,
    )

    monkeypatch.setattr(
        auth_service_module,
        "settings",
        get_settings().model_copy(
            update={
                "EMAIL_VERIFICATION_REQUIRED": True,
            }
        ),
    )

    monkeypatch.setattr(
        evs_module,
        "settings",
        get_settings().model_copy(
            update={
                "EMAIL_VERIFICATION_REQUIRED": True,
            }
        ),
    )

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


def _build_service(db_session, email_service=None):

    from app.infrastructure.repositories.audit_log_repository import (
        SQLAlchemyAuditLogRepository,
    )

    from app.infrastructure.repositories.email_verification_token_repository import (
        SQLAlchemyEmailVerificationTokenRepository,
    )

    from app.infrastructure.repositories.user_repository import (
        SQLAlchemyUserRepository,
    )

    return (
        EmailVerificationService(
            SQLAlchemyEmailVerificationTokenRepository(
                db_session
            ),
            SQLAlchemyAuditLogRepository(
                db_session
            ),
            email_service=(
                email_service or RecordingEmailService()
            ),
        ),
        SQLAlchemyUserRepository(db_session),
    )


def _create_user(db_session, email="verify@example.com"):

    from app.domain.models.user import (
        User,
    )

    from app.services.auth.password_service import (
        Argon2PasswordService,
    )

    user = User(
        email=email,
        username=email.split("@")[0],
        password_hash=(
            Argon2PasswordService()
            .hash_password(
                "CorrectHorseBatteryStaple!2026"
            )
        ),
        is_verified=False,
    )

    db_session.add(user)

    db_session.commit()

    return user


def test_issue_for_sends_link_with_token(db_session):
    user = _create_user(db_session)

    email_service = RecordingEmailService()

    service, _ = _build_service(
        db_session,
        email_service=email_service,
    )

    service.issue_for(user)

    assert len(email_service.sent) == 1

    body = email_service.sent[0]["body"]

    assert "verify-email?token=" in body

    token = body.split("token=")[1].strip()

    assert token


def test_issue_for_skips_verified_users(db_session):
    user = _create_user(db_session)
    user.is_verified = True

    db_session.commit()

    email_service = RecordingEmailService()

    service, _ = _build_service(
        db_session,
        email_service=email_service,
    )

    assert service.issue_for(user) is None

    assert email_service.sent == []


def test_verify_marks_account_verified(db_session):
    user = _create_user(db_session)

    email_service = RecordingEmailService()

    service, _ = _build_service(
        db_session,
        email_service=email_service,
    )

    service.issue_for(user)

    token = (
        email_service.sent[0]["body"]
        .split("token=")[1]
        .strip()
    )

    service.verify(token)

    assert user.is_verified is True


def test_verify_rejects_bad_token(db_session):
    user = _create_user(db_session)

    service, _ = _build_service(db_session)

    from app.core.exceptions import (
        EmailVerificationTokenInvalidError,
    )

    with pytest.raises(
        EmailVerificationTokenInvalidError
    ):
        service.verify("not-a-real-token")


def test_verify_token_is_one_time(db_session):
    user = _create_user(db_session)

    email_service = RecordingEmailService()

    service, _ = _build_service(
        db_session,
        email_service=email_service,
    )

    service.issue_for(user)

    token = (
        email_service.sent[0]["body"]
        .split("token=")[1]
        .strip()
    )

    service.verify(token)

    from app.core.exceptions import (
        EmailVerificationTokenInvalidError,
    )

    with pytest.raises(
        EmailVerificationTokenInvalidError
    ):
        service.verify(token)


def test_api_register_succeeds(client):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "apiverify@example.com",
            "username": "apiverify",
            "password": (
                "CorrectHorseBatteryStaple!2026"
            ),
        },
    )

    assert response.status_code == 200


def test_api_login_gated_until_verified(client):
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "apiverify2@example.com",
            "username": "apiverify2",
            "password": (
                "CorrectHorseBatteryStaple!2026"
            ),
        },
    )

    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "apiverify2@example.com",
            "password": (
                "CorrectHorseBatteryStaple!2026"
            ),
        },
    )

    assert response.status_code == 401

    assert "verified" in response.json()["detail"]


def test_api_verify_endpoint_rejects_bad_token(
    client,
):
    response = client.post(
        "/api/v1/auth/verify-email",
        json={"token": "garbage"},
    )

    assert response.status_code == 401


def test_api_resend_verification_no_enumeration(
    client,
):
    response = client.post(
        "/api/v1/auth/resend-verification",
        json={
            "email": "does-not-exist@example.com",
        },
    )

    assert response.status_code == 200
