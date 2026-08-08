from fastapi import Depends

from app.api.dependencies.repositories import (
    get_audit_repository,
    get_email_verification_token_repository,
    get_mfa_recovery_code_repository,
    get_refresh_token_repository,
    get_role_repository,
    get_session_repository,
    get_user_repository,
    get_webauthn_credential_repository,
    get_app_setting_repository,
)

from app.api.dependencies.jwt import (
    get_jwt_service,
)

from app.api.dependencies.storage import (
    get_email_service,
)

from app.services.auth.auth_service import (
    AuthService,
)

from app.services.auth.mfa_service import (
    MfaService,
)

from app.services.auth.admin_user_service import (
    AdminUserService,
)

from app.services.auth.email_verification_service import (
    EmailVerificationService,
)

from app.services.auth.webauthn_service import (
    WebAuthnService,
)


def get_admin_user_service(
    user_repository=Depends(
        get_user_repository
    ),
    role_repository=Depends(
        get_role_repository
    ),
    session_repository=Depends(
        get_session_repository
    ),
    refresh_repository=Depends(
        get_refresh_token_repository
    ),
    audit_repository=Depends(
        get_audit_repository
    ),
):

    return AdminUserService(
        user_repository,
        role_repository,
        session_repository,
        refresh_repository,
        audit_repository,
    )


def get_mfa_service(
    user_repository=Depends(
        get_user_repository
    ),
    recovery_code_repository=Depends(
        get_mfa_recovery_code_repository
    ),
    audit_repository=Depends(
        get_audit_repository
    ),
):

    return MfaService(
        user_repository,
        recovery_code_repository,
        audit_repository,
    )


def get_email_verification_service(
    token_repository=Depends(
        get_email_verification_token_repository
    ),
    audit_repository=Depends(
        get_audit_repository
    ),
    email_service=Depends(
        get_email_service
    ),
):

    return EmailVerificationService(
        token_repository,
        audit_repository,
        email_service,
    )


def get_auth_service(
    user_repository=Depends(
        get_user_repository
    ),
    role_repository=Depends(
        get_role_repository
    ),
    session_repository=Depends(
        get_session_repository
    ),
    refresh_repository=Depends(
        get_refresh_token_repository
    ),
    audit_repository=Depends(
        get_audit_repository
    ),
    jwt_service=Depends(
        get_jwt_service
    ),
    mfa_service=Depends(
        get_mfa_service
    ),
    verification_service=Depends(
        get_email_verification_service
    ),
):

    return AuthService(
        user_repository,
        role_repository,
        session_repository,
        refresh_repository,
        audit_repository,
        jwt_service,
        mfa_service,
        verification_service,
    )
