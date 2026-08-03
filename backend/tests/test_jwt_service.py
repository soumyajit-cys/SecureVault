import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base

from app.infrastructure.repositories.jwt_signing_key_repository import (
    SQLAlchemyJwtSigningKeyRepository,
)

from app.services.auth.jwt_key_service import (
    JwtKeyService,
)

from app.services.auth.jwt_service import (
    JWTService,
)


@pytest.fixture
def jwt_service():

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

        yield JWTService(
            key_service
        )

        session.commit()

    finally:

        session.close()

        engine.dispose()


def test_jwt_encode_decode(
    jwt_service,
):

    token = jwt_service.create_token(
        {
            "sub": "1",
            "email": "test@test.com",
            "session_id": "session",
            "token_type": "access",
        },
        __import__(
            "datetime"
        ).timedelta(
            minutes=10
        ),
    )

    decoded = (
        jwt_service.decode_token(
            token
        )
    )

    assert (
        decoded.sub == "1"
    )

    assert (
        decoded.token_type
        == "access"
    )


def test_jwt_carries_key_id(
    jwt_service,
):

    token = jwt_service.create_token(
        {
            "sub": "1",
            "email": "test@test.com",
            "session_id": "session",
            "token_type": "access",
        },
        __import__(
            "datetime"
        ).timedelta(
            minutes=10
        ),
    )

    import jwt as pyjwt

    header = pyjwt.get_unverified_header(
        token
    )

    assert "kid" in header

    assert header["kid"].startswith(
        "sv-"
    )


def test_jwt_survives_rotation(
    jwt_service,
):

    token = jwt_service.create_token(
        {
            "sub": "1",
            "email": "test@test.com",
            "session_id": "session",
            "token_type": "access",
        },
        __import__(
            "datetime"
        ).timedelta(
            minutes=10
        ),
    )

    jwt_service.key_service.rotate()

    decoded = (
        jwt_service.decode_token(
            token
        )
    )

    assert (
        decoded.sub == "1"
    )