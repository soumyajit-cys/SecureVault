from uuid import uuid4

from app.schemas.auth_context import (
    AuthContext,
)

from app.services.auth.token_service import (
    TokenService,
)


def test_access_token_creation():

    context = AuthContext(
        user_id=uuid4(),
        email="test@test.com",
        session_id="session",
        roles=["User"],
        permissions=[],
    )

    service = TokenService()

    token = (
        service.create_access_token(
            context
        )
    )

    assert isinstance(
        token,
        str,
    )


def test_refresh_token_creation():

    context = AuthContext(
        user_id=uuid4(),
        email="test@test.com",
        session_id="session",
        roles=["User"],
        permissions=[],
    )

    service = TokenService()

    token = (
        service.create_refresh_token(
            context
        )
    )

    assert isinstance(
        token,
        str,
    )