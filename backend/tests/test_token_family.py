from app.services.auth.token_utils import (
    generate_token_family,
)


def test_token_family_generation():

    family_1 = (
        generate_token_family()
    )

    family_2 = (
        generate_token_family()
    )

    assert family_1 != family_2