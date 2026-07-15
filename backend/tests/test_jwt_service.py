from app.services.auth.jwt_service import (
    JWTService,
)


def test_jwt_encode_decode():

    service = JWTService()

    token = service.create_token(
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
        service.decode_token(
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