from uuid import uuid4

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base

from app.schemas.auth_context import (
    AuthContext,
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

from app.services.auth.token_service import (
    TokenService,
)


@pytest.fixture
def token_service():

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

    try:

        key_service = JwtKeyService(
            SQLAlchemyJwtSigningKeyRepository(
                session
            )
        )

        yield TokenService(
            JWTService(
                key_service
            )
        )

        session.commit()

    finally:

        session.close()

        engine.dispose()


def test_access_token_creation(
    token_service,
):

    context = AuthContext(
        user_id=uuid4(),
        email="test@test.com",
        session_id="session",
        roles=["User"],
        permissions=[],
    )

    token = (
        token_service.create_access_token(
            context
        )
    )

    assert isinstance(
        token,
        str,
    )


def test_refresh_token_creation(
    token_service,
):

    context = AuthContext(
        user_id=uuid4(),
        email="test@test.com",
        session_id="session",
        roles=["User"],
        permissions=[],
    )

    token = (
        token_service.create_refresh_token(
            context
        )
    )

    assert isinstance(
        token,
        str,
    )