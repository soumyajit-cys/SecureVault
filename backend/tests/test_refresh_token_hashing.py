from app.services.auth.token_utils import (
    hash_token,
)


def test_token_hashing():

    token = (
        "securevault_refresh"
    )

    hashed = hash_token(
        token
    )

    assert hashed != token

    assert len(hashed) == 64