def test_auth_module_import():

    from app.services.auth.auth_service import (
        AuthService,
    )

    assert AuthService