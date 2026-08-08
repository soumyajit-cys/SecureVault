from uuid import UUID

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import Request

from app.api.dependencies.auth import (
    get_auth_service,
    get_email_verification_service,
    get_mfa_service,
    get_webauthn_service,
)
from app.api.dependencies.current_user import (
    get_current_session_id,
    get_current_user,
)
from app.api.dependencies.jwt import (
    get_jwt_service,
)
from app.api.dependencies.repositories import (
    get_user_repository,
)
from app.api.dependencies.storage import (
    get_password_reset_service,
)

from app.schemas.auth import (
    EmailVerificationRequest,
    LoginRequest,
    MfaDisableRequest,
    MfaEnableRequest,
    MfaVerifyRequest,
    PasswordResetConfirmRequest,
    PasswordResetRequest,
    RefreshRequest,
    RegisterRequest,
    LogoutRequest,
)

from app.schemas.webauthn import (
    PasskeyLoginBeginRequest,
    PasskeyLoginCompleteRequest,
    PasskeyRegistrationCompleteRequest,
    PasskeyRemoveRequest,
)

from app.schemas.user import (
    PasswordChangeRequest,
)

from app.core.exceptions import (
    NotFoundError,
    WebAuthnVerificationFailedError,
)

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


def _client_ip(request: Request) -> str | None:

    forward_for = (
        request.headers.get(
            "X-Forwarded-For"
        )
    )

    if forward_for:
        return (
            forward_for.split(",")[0]
            .strip()
        )

    return (
        request.client.host
        if request.client
        else None
    )


@router.post("/register")
def register(
    payload: RegisterRequest,
    auth_service=Depends(
        get_auth_service
    ),
):
    user = auth_service.register(
        payload.email,
        payload.username,
        payload.password,
    )

    return {
        "id": str(user.id),
        "email": user.email,
        "username": user.username,
        "message": (
            "Account created. Please sign in."
        ),
    }


@router.post("/login")
def login(
    payload: LoginRequest,
    request: Request,
    auth_service=Depends(
        get_auth_service
    ),
):
    return auth_service.login(
        payload.email,
        payload.password,
        _client_ip(request),
        request.headers.get("User-Agent"),
    )


@router.post("/mfa/verify")
def verify_mfa_login(
    payload: MfaVerifyRequest,
    request: Request,
    auth_service=Depends(
        get_auth_service
    ),
):
    return auth_service.complete_login_with_mfa(
        payload.mfa_token,
        payload.code,
        _client_ip(request),
        request.headers.get("User-Agent"),
    )


@router.post("/refresh")
def refresh(
    payload: RefreshRequest,
    auth_service=Depends(
        get_auth_service
    ),
):
    return auth_service.refresh(
        payload.refresh_token
    )


@router.post("/logout")
def logout(
    payload: LogoutRequest,
    auth_service=Depends(
        get_auth_service
    ),
):
    return auth_service.logout(
        payload.refresh_token
    )


@router.post("/change-password")
def change_password(
    payload: PasswordChangeRequest,
    current_user=Depends(
        get_current_user
    ),
    auth_service=Depends(
        get_auth_service
    ),
    session_id=Depends(
        get_current_session_id
    ),
):
    return {
        "message": "Password changed",
        "changed": auth_service.change_password(
            current_user,
            payload.current_password,
            payload.new_password,
            keep_session_id=session_id,
        ),
    }


# -------------------------------------------------
# MFA
# -------------------------------------------------

@router.get("/mfa/status")
def mfa_status(
    current_user=Depends(
        get_current_user
    ),
):
    return {
        "enabled": bool(
            current_user.totp_enabled
        ),
        "enabled_at": current_user.totp_enabled_at,
    }


@router.post("/mfa/setup")
def mfa_setup(
    current_user=Depends(
        get_current_user
    ),
    mfa_service=Depends(
        get_mfa_service
    ),
):
    if current_user.totp_enabled:
        raise HTTPException(
            status_code=409,
            detail="MFA is already enabled",
        )

    return mfa_service.start_setup(
        current_user
    )


@router.post("/mfa/enable")
def mfa_enable(
    payload: MfaEnableRequest,
    current_user=Depends(
        get_current_user
    ),
    mfa_service=Depends(
        get_mfa_service
    ),
):
    if current_user.totp_enabled:
        raise HTTPException(
            status_code=409,
            detail="MFA is already enabled",
        )

    return mfa_service.confirm_setup(
        current_user,
        payload.code,
        payload.secret,
    )


@router.post("/mfa/disable")
def mfa_disable(
    payload: MfaDisableRequest,
    current_user=Depends(
        get_current_user
    ),
    mfa_service=Depends(
        get_mfa_service
    ),
):
    if not current_user.totp_enabled:
        raise HTTPException(
            status_code=409,
            detail="MFA is not enabled",
        )

    mfa_service.disable(
        current_user,
        payload.code,
    )

    return {"message": "MFA disabled"}


# -------------------------------------------------
# Passkeys (WebAuthn)
# -------------------------------------------------

@router.post("/passkeys/register/begin")
def passkey_register_begin(
    current_user=Depends(
        get_current_user
    ),
    webauthn_service=Depends(
        get_webauthn_service
    ),
):
    return {
        "options": (
            webauthn_service
            .generate_registration_options(
                current_user
            )
        )
    }


@router.post("/passkeys/register/complete")
def passkey_register_complete(
    payload: PasskeyRegistrationCompleteRequest,
    current_user=Depends(
        get_current_user
    ),
    webauthn_service=Depends(
        get_webauthn_service
    ),
):
    try:

        credential = (
            webauthn_service
            .verify_registration(
                current_user,
                payload.response,
                payload.device_label,
            )
        )

    except WebAuthnVerificationFailedError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    return {
        "message": "Passkey registered",
        "credential_id": (
            credential.credential_id
        ),
    }


@router.get("/passkeys")
def passkey_list(
    current_user=Depends(
        get_current_user
    ),
    webauthn_service=Depends(
        get_webauthn_service
    ),
):
    return [
        {
            "id": item.credential_id,
            "device_label": item.device_label,
            "created_at": (
                item.created_at.isoformat()
                if item.created_at
                else None
            ),
            "last_used_at": (
                item.last_used_at.isoformat()
                if item.last_used_at
                else None
            ),
        }
        for item in (
            webauthn_service.list_credentials(
                current_user.id
            )
        )
    ]


@router.delete("/passkeys")
def passkey_remove(
    payload: PasskeyRemoveRequest,
    current_user=Depends(
        get_current_user
    ),
    webauthn_service=Depends(
        get_webauthn_service
    ),
):
    removed = (
        webauthn_service.remove_credential(
            current_user.id,
            payload.credential_id,
        )
    )

    if not removed:
        raise HTTPException(
            status_code=404,
            detail="Credential not found",
        )

    return {
        "message": "Passkey removed",
    }


@router.post("/passkeys/login/begin")
def passkey_login_begin(
    payload: PasskeyLoginBeginRequest,
    webauthn_service=Depends(
        get_webauthn_service
    ),
    user_repository=Depends(
        get_user_repository
    ),
):
    user = None

    if payload.email:

        from app.domain.models.user import User

        found = (
            user_repository.get_by_email(
                payload.email
            )
        )

        if found is not None:
            user = found

    return {
        "options": (
            webauthn_service
            .generate_authentication_options(
                user
            )
        )
    }


@router.post("/passkeys/login/complete")
def passkey_login_complete(
    payload: PasskeyLoginCompleteRequest,
    request: Request,
    webauthn_service=Depends(
        get_webauthn_service
    ),
    auth_service=Depends(
        get_auth_service
    ),
):
    try:

        user = (
            webauthn_service
            .verify_authentication(
                payload.response
            )
        )

    except WebAuthnVerificationFailedError as exc:
        raise HTTPException(
            status_code=401,
            detail=str(exc),
        ) from exc

    return auth_service.complete_passkey_login(
        user,
        client_ip=_client_ip(request),
        user_agent=request.headers.get(
            "User-Agent"
        ),
    )


# -------------------------------------------------
# Password reset
# -------------------------------------------------

@router.post("/password-reset/request")
def password_reset_request(
    payload: PasswordResetRequest,
    reset_service=Depends(
        get_password_reset_service
    ),
):
    reset_service.request_reset(
        payload.email
    )

    return {
        "message": (
            "If that email exists, a reset link "
            "has been sent."
        )
    }


@router.post("/password-reset/confirm")
def password_reset_confirm(
    payload: PasswordResetConfirmRequest,
    reset_service=Depends(
        get_password_reset_service
    ),
):
    reset_service.reset_password(
        payload.token,
        payload.new_password,
    )

    return {
        "message": (
            "Password reset. Please sign in "
            "with your new password."
        )
    }


# -------------------------------------------------
# Email verification
# -------------------------------------------------

@router.post("/verify-email")
def verify_email(
    payload: EmailVerificationRequest,
    verification_service=Depends(
        get_email_verification_service
    ),
):
    verification_service.verify(
        payload.token
    )

    return {
        "message": (
            "Email verified. You can now sign in."
        )
    }


@router.post("/resend-verification")
def resend_verification(
    payload: PasswordResetRequest,
    user_repository=Depends(
        get_user_repository
    ),
    verification_service=Depends(
        get_email_verification_service
    ),
):
    # Resend only makes sense before sign-in, so it
    # is keyed by the (rate-limited) email address
    # rather than an authenticated session.
    user = (
        user_repository.get_by_email(
            payload.email
        )
    )

    if (
        user
        and not user.is_verified
        and user.is_active
    ):
        verification_service.issue_for(
            user
        )

    return {
        "message": (
            "If that account is pending "
            "verification, a new link has been sent."
        )
    }


# -------------------------------------------------
# Session management
# -------------------------------------------------

@router.get("/sessions")
def list_sessions(
    current_user=Depends(
        get_current_user
    ),
    auth_service=Depends(
        get_auth_service
    ),
):
    from app.schemas.session import (
        SessionResponse,
    )

    sessions = (
        auth_service.list_sessions(
            current_user
        )
    )

    return [
        SessionResponse(
            id=s.id,
            created_at=s.created_at,
            updated_at=s.updated_at,
            session_identifier=(
                s.session_identifier
            ),
            device_name=s.device_name,
            ip_address=s.ip_address,
            user_agent=s.user_agent,
            revoked=s.revoked,
            expires_at=s.expires_at,
            last_seen_at=s.last_seen_at,
        )
        for s in sessions
    ]


@router.delete("/sessions/{session_id}")
def revoke_session(
    session_id: UUID,
    current_user=Depends(
        get_current_user
    ),
    auth_service=Depends(
        get_auth_service
    ),
):
    try:
        auth_service.revoke_session(
            current_user,
            session_id,
        )
    except NotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    return {"message": "Session revoked"}


@router.post("/sessions/revoke-all")
def revoke_all_sessions(
    request: Request,
    current_user=Depends(
        get_current_user
    ),
    auth_service=Depends(
        get_auth_service
    ),
    jwt_service=Depends(
        get_jwt_service
    ),
):
    current_identifier = None

    auth_header = (
        request.headers.get(
            "Authorization"
        )
    )

    if auth_header and auth_header.startswith(
        "Bearer "
    ):
        try:
            claims = jwt_service.decode_token(
                auth_header[7:]
            )
            current_identifier = (
                claims.session_id
            )
        except Exception:
            current_identifier = None

    count = auth_service.revoke_all_sessions(
        current_user,
        exclude_session_identifier=(
            current_identifier
        ),
    )

    return {
        "message": (
            f"{count} other session(s) revoked"
        )
    }
