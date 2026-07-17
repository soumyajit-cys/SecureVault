from app.services.auth.token_utils import (
    generate_session_id,
)


def test_session_generation():

    sid_1 = (
        generate_session_id()
    )

    sid_2 = (
        generate_session_id()
    )

    assert sid_1 != sid_2