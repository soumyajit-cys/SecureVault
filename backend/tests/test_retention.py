from datetime import UTC
from datetime import datetime
from datetime import timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base
from app.scripts.initialize_identity import (
    seed_permissions,
    seed_roles,
)
from app.services.audit_service import (
    AuditService,
)

from app.domain.models.audit_log import (
    AuditLog,
)
from app.domain.models.session import (
    Session,
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


def _retention(db_session):

    from app.services.data_retention_service import (
        DataRetentionService,
    )

    from app.infrastructure.repositories.audit_log_repository import (
        SQLAlchemyAuditLogRepository,
    )

    from app.infrastructure.repositories.email_verification_token_repository import (
        SQLAlchemyEmailVerificationTokenRepository,
    )

    from app.infrastructure.repositories.password_reset_token_repository import (
        SQLAlchemyPasswordResetTokenRepository,
    )

    from app.infrastructure.repositories.refresh_token_repository import (
        SQLAlchemyRefreshTokenRepository,
    )

    from app.infrastructure.repositories.session_repository import (
        SQLAlchemySessionRepository,
    )

    return DataRetentionService(
        SQLAlchemyAuditLogRepository(db_session),
        SQLAlchemySessionRepository(db_session),
        SQLAlchemyRefreshTokenRepository(db_session),
        SQLAlchemyPasswordResetTokenRepository(db_session),
        SQLAlchemyEmailVerificationTokenRepository(db_session),
    )


def test_purges_stale_audit_logs(db_session):

    audit = AuditService(
        _audit_repo(db_session)
    )

    audit.log(None, "event.old")
    audit.log(None, "event.new")

    db_session.query(AuditLog).filter(
        AuditLog.action == "event.old"
    ).update(
        {
            "created_at": (
                datetime.now(UTC)
                - timedelta(days=200)
            )
        }
    )

    db_session.commit()

    summary = _retention(db_session).run(
        retention_days=90
    )

    assert summary["audit_logs"] == 1

    remaining = db_session.query(
        AuditLog
    ).all()

    assert [e.action for e in remaining] == [
        "event.new"
    ]


def test_keeps_active_sessions(db_session):

    service = _retention(db_session)

    active = _session(
        db_session,
        revoked=False,
        days_ago=30,
    )

    revoked = _session(
        db_session,
        revoked=True,
        days_ago=30,
    )

    expired = _session(
        db_session,
        revoked=False,
        days_ago=30,
        expired=True,
    )

    summary = service.run(retention_days=10)

    assert summary["sessions"] == 2

    left = {
        s.session_identifier
        for s in db_session.query(Session).all()
    }

    assert active.session_identifier in left

    assert revoked.session_identifier not in left

    assert expired.session_identifier not in left


def test_keeps_recent_revoked_tokens(db_session):

    service = _retention(db_session)

    _refresh_token(
        db_session,
        revoked=True,
        days_ago=5,
    )

    old = _refresh_token(
        db_session,
        revoked=True,
        days_ago=200,
    )

    summary = service.run(retention_days=90)

    assert summary["refresh_tokens"] == 1

    from app.domain.models.refresh_token import (
        RefreshToken,
    )

    left = (
        db_session.query(RefreshToken)
        .filter(RefreshToken.revoked.is_(False))
        .count()
    )

    assert left == 0

    assert (
        db_session.query(RefreshToken)
        .filter(
            RefreshToken.revoked.is_(True)
        )
        .count()
    ) == 1

    assert old.token_hash


def _audit_repo(db_session):

    from app.infrastructure.repositories.audit_log_repository import (
        SQLAlchemyAuditLogRepository,
    )

    return SQLAlchemyAuditLogRepository(db_session)


def _session(
    db_session,
    revoked: bool,
    days_ago: int,
    expired: bool = False,
):

    import uuid

    now = datetime.now(UTC)

    s = Session(
        session_identifier=str(uuid.uuid4()),
        expires_at=(
            now - timedelta(days=1)
            if expired
            else now + timedelta(days=7)
        ),
        revoked=revoked,
        created_at=now - timedelta(
            days=days_ago
        ),
        user_id=None,
    )

    db_session.add(s)

    db_session.commit()

    return s


def _refresh_token(
    db_session,
    revoked: bool,
    days_ago: int,
):

    import uuid

    from app.domain.models.refresh_token import (
        RefreshToken,
    )

    now = datetime.now(UTC)

    token = RefreshToken(
        token_hash=str(uuid.uuid4()),
        token_family=str(uuid.uuid4()),
        session_id=str(uuid.uuid4()),
        expires_at=now + timedelta(days=7),
        revoked=revoked,
        created_at=now - timedelta(
            days=days_ago
        ),
        user_id=None,
    )

    db_session.add(token)

    db_session.commit()

    return token
