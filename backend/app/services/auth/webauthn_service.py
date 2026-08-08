import secrets
from datetime import UTC
from datetime import datetime
from uuid import UUID

from webauthn import (
    generate_authentication_options,
    generate_registration_options,
    verify_authentication_response,
    verify_registration_response,
)
from webauthn.helpers import (
    base64url_to_bytes,
    bytes_to_base64url,
)
from webauthn.helpers.structs import (
    AuthenticatorSelectionCriteria,
    PublicKeyCredentialDescriptor,
    ResidentKeyRequirement,
    UserVerificationRequirement,
)

from app.core.config import get_settings
from app.core.exceptions import (
    WebAuthnVerificationFailedError,
)
from app.domain.constants.audit_events import (
    PASSKEY_LOGIN,
    PASSKEY_REGISTERED,
    PASSKEY_REMOVED,
    PASSKEY_VERIFY_FAILED,
)
from app.domain.models.user import User
from app.domain.models.webauthn_credential import WebAuthnCredential
from app.services.audit_service import AuditService

settings = get_settings()

# Challenges live here for the duration of the
# ceremony; they are single-use and time-boxed.
_CHALLENGE_TTL_SECONDS = 120


class WebAuthnChallengeStore:
    """
    In-memory single-use challenge store.

    The session table could host these, but the
    in-memory map keeps the ceremony dependency-free
    and is acceptable because a challenge is only
    useful to the caller that holds the browser
    session it was issued to.
    """

    def __init__(self) -> None:
        self._items: dict[str, dict] = {}

    def put(
        self,
        key: str,
        challenge: bytes,
        user_id: UUID,
        purpose: str,
    ) -> None:
        self._items[key] = {
            "challenge": challenge,
            "user_id": str(user_id),
            "purpose": purpose,
            "expires_at": (
                datetime.now(UTC).timestamp()
                + _CHALLENGE_TTL_SECONDS
            ),
        }

    def pop(
        self,
        key: str,
        expected_purpose: str,
    ) -> tuple[bytes, UUID] | None:
        """
        Remove and return the stored challenge if it
        exists, matches the expected purpose and has
        not expired. Returns None otherwise.
        """

        item = self._items.pop(key, None)

        if item is None:
            return None

        if (
            item["expires_at"]
            < datetime.now(UTC).timestamp()
        ):
            return None

        if (
            item["purpose"]
            != expected_purpose
        ):
            return None

        return (
            item["challenge"],
            UUID(item["user_id"]),
        )

    def purge_expired(self) -> None:
        now = datetime.now(UTC).timestamp()

        expired = [
            key
            for key, item in self._items.items()
            if item["expires_at"] < now
        ]

        for key in expired:
            self._items.pop(key, None)


challenge_store = WebAuthnChallengeStore()


class WebAuthnService:
    """
    Passkey registration and authentication ceremonies
    (FIDO2 / WebAuthn Level 2), plus MFA policy state.
    """

    def __init__(
        self,
        credential_repository,
        setting_repository,
        audit_repository,
    ) -> None:

        self.credentials = credential_repository

        self.settings_repo = setting_repository

        self.audit_service = (
            AuditService(audit_repository)
        )

    # -------------------------------------------------
    # MFA enforcement policy
    # -------------------------------------------------

    MFA_POLICY_KEY = "mfa_enforcement_mode"

    def enforcement_mode(self) -> str:
        """
        Runtime policy (stored) falls back to the
        configured default.
        """

        setting = self.settings_repo.get(
            self.MFA_POLICY_KEY
        )

        if setting is None:
            return settings.MFA_ENFORCEMENT_MODE

        return setting.value

    def set_enforcement_mode(
        self,
        mode: str,
    ) -> str:
        if mode not in {
            "optional",
            "required",
        }:
            raise ValueError(
                "mode must be 'optional' or 'required'"
            )

        self.settings_repo.set(
            self.MFA_POLICY_KEY,
            mode,
        )

        return mode

    def user_has_mfa(
        self,
        user: User,
    ) -> bool:
        if user.totp_enabled:
            return True

        return bool(
            self.credentials.list_for_user(
                user.id
            )
        )

    # -------------------------------------------------
    # Registration
    # -------------------------------------------------

    def generate_registration_options(
        self,
        user: User,
    ) -> dict:
        """
        Begin a passkey enrollment ceremony for a
        signed-in user.
        """

        challenge = secrets.token_bytes(32)

        existing = (
            self.credentials.list_for_user(
                user.id
            )
        )

        exclude = [
            PublicKeyCredentialDescriptor(
                id=base64url_to_bytes(
                    item.credential_id
                )
            )
            for item in existing
        ]

        options = generate_registration_options(
            rp_id=settings.WEBAUTHN_RP_ID,
            rp_name=settings.WEBAUTHN_RP_NAME,
            user_id=str(user.id).encode(),
            user_name=user.email,
            user_display_name=user.username,
            challenge=challenge,
            exclude_credentials=exclude or None,
            authenticator_selection=AuthenticatorSelectionCriteria(
                resident_key=ResidentKeyRequirement.REQUIRED,
                user_verification=(
                    UserVerificationRequirement.REQUIRED
                ),
            ),
        )

        challenge_store.put(
            f"register:{user.id}",
            challenge,
            user.id,
            "register",
        )

        return options.model_dump()

    def verify_registration(
        self,
        user: User,
        response: dict,
        device_label: str,
    ) -> WebAuthnCredential:
        """
        Verify the browser's attestation response and
        persist the new credential. Single-use, so a
        captured response cannot be replayed.
        """

        stored = challenge_store.pop(
            f"register:{user.id}",
            "register",
        )

        if stored is None:
            raise WebAuthnVerificationFailedError(
                "Registration challenge expired or "
                "already used"
            )

        expected_challenge, expected_user = stored

        if expected_user != user.id:
            raise WebAuthnVerificationFailedError(
                "Registration challenge mismatch"
            )

        try:

            verified = verify_registration_response(
                credential=response,
                expected_challenge=expected_challenge,
                expected_rp_id=settings.WEBAUTHN_RP_ID,
                expected_origin=settings.WEBAUTHN_ORIGIN,
                require_user_verification=True,
            )

        except Exception as exc:
            self.audit_service.log(
                user.id,
                PASSKEY_VERIFY_FAILED,
                details=str(exc),
            )
            raise WebAuthnVerificationFailedError(
                f"Registration verification failed: {exc}"
            ) from exc

        credential_id = bytes_to_base64url(
            verified.credential_id
        )

        if (
            self.credentials.get_by_credential_id(
                credential_id
            )
        ):
            raise WebAuthnVerificationFailedError(
                "Credential already registered"
            )

        entity = WebAuthnCredential(
            user_id=user.id,
            credential_id=credential_id,
            public_key=bytes_to_base64url(
                verified.credential_public_key
            ),
            sign_count=verified.sign_count,
            device_label=device_label
            or "Security key",
            aaguid=str(
                verified.aaguid
            ) if verified.aaguid else None,
            last_used_at=datetime.now(UTC),
        )

        created = (
            self.credentials.create(entity)
        )

        self.audit_service.log(
            user.id,
            PASSKEY_REGISTERED,
            details=f"credential_id={credential_id}",
        )

        return created

    # -------------------------------------------------
    # Authentication
    # -------------------------------------------------

    def generate_authentication_options(
        self,
        user: User | None,
    ) -> dict:
        """
        Begin a passkey login. With a user, allow
        their registered credentials; otherwise
        request a discoverable credential.
        """

        challenge = secrets.token_bytes(32)

        allow: list[
            PublicKeyCredentialDescriptor
        ] | None = None

        if user is not None:

            allow = [
                PublicKeyCredentialDescriptor(
                    id=base64url_to_bytes(
                        item.credential_id
                    )
                )
                for item in (
                    self.credentials.list_for_user(
                        user.id
                    )
                )
            ]

        options = generate_authentication_options(
            rp_id=settings.WEBAUTHN_RP_ID,
            challenge=challenge,
            allow_credentials=allow or None,
            user_verification=(
                UserVerificationRequirement.REQUIRED
            ),
        )

        challenge_store.put(
            "login",
            challenge,
            user.id if user else UUID(int=0),
            "login",
        )

        return options.model_dump()

    def verify_authentication(
        self,
        response: dict,
    ) -> User:
        """
        Verify a passkey assertion and return the
        owning user. Sign-count regression (cloned
        authenticator) is rejected.
        """

        stored = challenge_store.pop(
            "login",
            "login",
        )

        if stored is None:
            raise WebAuthnVerificationFailedError(
                "Authentication challenge expired or "
                "already used"
            )

        expected_challenge, _ = stored

        try:

            raw_id = bytes_to_base64url(
                base64url_to_bytes(
                    response["rawId"]
                    or response["id"]
                )
            )

        except Exception as exc:
            raise WebAuthnVerificationFailedError(
                f"Malformed credential id: {exc}"
            ) from exc

        credential = (
            self.credentials.get_by_credential_id(
                raw_id
            )
        )

        if credential is None:
            raise WebAuthnVerificationFailedError(
                "Unknown credential"
            )

        try:

            verified = verify_authentication_response(
                credential=response,
                expected_challenge=expected_challenge,
                expected_rp_id=settings.WEBAUTHN_RP_ID,
                expected_origin=settings.WEBAUTHN_ORIGIN,
                credential_public_key=(
                    base64url_to_bytes(
                        credential.public_key
                    )
                ),
                credential_current_sign_count=(
                    credential.sign_count
                ),
                require_user_verification=True,
            )

        except Exception as exc:
            self.audit_service.log(
                credential.user_id,
                PASSKEY_VERIFY_FAILED,
                details=f"credential_id={raw_id}",
            )
            raise WebAuthnVerificationFailedError(
                f"Authentication verification failed: {exc}"
            ) from exc

        if (
            verified.new_sign_count
            <= credential.sign_count
            and credential.sign_count > 0
        ):
            raise WebAuthnVerificationFailedError(
                "Credential counter regression - "
                "possible cloned authenticator"
            )

        credential.sign_count = (
            verified.new_sign_count
        )

        credential.last_used_at = (
            datetime.now(UTC)
        )

        self.credentials.update(credential)

        user = credential.user

        self.audit_service.log(
            user.id,
            PASSKEY_LOGIN,
            details=f"credential_id={raw_id}",
        )

        return user

    # -------------------------------------------------
    # Credential management
    # -------------------------------------------------

    def list_credentials(
        self,
        user_id: UUID,
    ) -> list[WebAuthnCredential]:
        return (
            self.credentials.list_for_user(
                user_id
            )
        )

    def remove_credential(
        self,
        user_id: UUID,
        credential_id: str,
    ) -> bool:
        """
        Delete one of the user's credentials.

        Returns False when the credential does not
        belong to the user (no information leak about
        other users' credentials).
        """

        owned = (
            self.credentials.get_owned(
                user_id,
                credential_id,
            )
        )

        if owned is None:
            return False

        self.credentials.delete(owned)

        self.audit_service.log(
            user_id,
            PASSKEY_REMOVED,
            details=(
                f"credential_id={credential_id}"
            ),
        )

        return True
