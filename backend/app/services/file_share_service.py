from __future__ import annotations

import base64
from datetime import UTC, datetime
from uuid import UUID

from app.core.exceptions import NotFoundError
from app.crypto.rsa.hybrid_encryptor import HybridEncryptor
from app.crypto.rsa.rsa_service import RSAService
from app.domain.models.file_share import FileShare
from app.domain.models.stored_file import StoredFile
from app.services.encryption.container_serializer import (
    ContainerSerializer,
)
from app.services.key_management_service import (
    KeyManagementService,
    KeyNotFoundError,
)


class ShareError(Exception):
    pass


class ShareNotFoundError(ShareError):
    pass


class SharePermissionError(ShareError):
    pass


class ShareService:
    """
    Multi-user sharing via per-grantee session-key wraps.

    Design
    ------

    - The payload is encrypted once with a fresh AES-256 session key.
    - The container stores one wrapped copy under the owner's RSA
      public key (existing flow, unchanged).
    - Sharing unwraps that session key with the owner's private key
      and wraps a *copy* under the grantee's active RSA public key.
      The copy lives in ``file_shares.wrapped_key``; the container
      bytes on disk are never modified and never re-encrypted.
    - Each grantee decrypts independently with their own private key.
    - Revocation marks the grant revoked; it does not rotate the
      session key (documented limitation).
    """

    def __init__(
        self,
        shares,
        stored_files,
        users,
        keys: KeyManagementService,
        storage=None,
        serializer: ContainerSerializer | None = None,
        hybrid: HybridEncryptor | None = None,
        rsa: RSAService | None = None,
    ) -> None:
        self._shares = shares
        self._files = stored_files
        self._users = users
        self._keys = keys
        self._storage = storage
        self._serializer = serializer or ContainerSerializer()
        self._hybrid = hybrid or HybridEncryptor()
        self._rsa = rsa or RSAService()

    # -------------------------------------------------
    # Share / revoke
    # -------------------------------------------------

    def share(
        self,
        owner_id: UUID,
        file_id: UUID,
        grantee_email: str,
    ) -> FileShare:
        stored = self._files.get_for_user(
            owner_id,
            file_id,
        )

        if stored is None:
            raise ShareNotFoundError(
                "Stored file not found."
            )

        if stored.key_id is None:
            raise ShareError(
                "File has no encryption key; cannot share."
            )

        email = (grantee_email or "").strip().lower()

        if not email:
            raise ShareError(
                "Grantee email is required."
            )

        grantee = self._users.get_by_email(email)

        if grantee is None:
            raise ShareNotFoundError(
                "Recipient not found."
            )

        if grantee.id == owner_id:
            raise ShareError(
                "Cannot share a file with yourself."
            )

        existing = self._shares.get_active(
            stored.id,
            grantee.id,
        )

        if existing is not None:
            return existing

        try:
            grantee_key = self._keys.get_active_for_user(
                grantee.id
            )
        except KeyNotFoundError as exc:
            raise ShareError(
                "Recipient has no active encryption key."
            ) from exc

        session_key = self._unwrap_owner_session_key(
            owner_id,
            stored,
        )

        grantee_public = self._rsa.load_public_key(
            grantee_key.public_key_pem.encode()
        )

        wrapped = self._hybrid.wrap_key(
            session_key,
            grantee_public,
        )

        grant = FileShare(
            file_id=stored.id,
            owner_id=owner_id,
            grantee_id=grantee.id,
            grantee_key_id=grantee_key.id,
            wrapped_key=base64.b64encode(wrapped).decode(),
            key_algorithm="RSA-4096-OAEP",
        )

        return self._shares.create(grant)

    def revoke(
        self,
        owner_id: UUID,
        file_id: UUID,
        grantee_id: UUID,
    ) -> FileShare:
        stored = self._files.get_for_user(
            owner_id,
            file_id,
        )

        if stored is None:
            raise ShareNotFoundError(
                "Stored file not found."
            )

        grant = self._shares.get_active(
            stored.id,
            grantee_id,
        )

        if grant is None:
            raise ShareNotFoundError(
                "Active share grant not found."
            )

        grant.revoked_at = datetime.now(UTC)

        return self._shares.update(grant)

    # -------------------------------------------------
    # Reads
    # -------------------------------------------------

    def list_for_file(
        self,
        owner_id: UUID,
        file_id: UUID,
        include_revoked: bool = True,
    ) -> tuple[StoredFile, list[FileShare]]:
        stored = self._files.get_for_user(
            owner_id,
            file_id,
        )

        if stored is None:
            raise ShareNotFoundError(
                "Stored file not found."
            )

        return stored, self._shares.list_for_file(
            stored.id,
            include_revoked=include_revoked,
        )

    def list_received(
        self,
        grantee_id: UUID,
    ) -> list[tuple[FileShare, StoredFile | None]]:
        grants = self._shares.list_received_for_user(
            grantee_id,
            include_revoked=False,
        )

        out: list[tuple[FileShare, StoredFile | None]] = []

        for grant in grants:
            # Owner-scoped lookup is wrong here; fetch by id so a
            # grantee can resolve a file they do not own.
            stored = self._files.get(grant.file_id)

            if stored is not None and stored.status != "active":
                continue

            out.append((grant, stored))

        return [
            (grant, stored)
            for grant, stored in out
            if stored is not None
        ]

    def list_sent(
        self,
        owner_id: UUID,
    ) -> list[FileShare]:
        return self._shares.list_sent_by_user(
            owner_id,
            include_revoked=True,
        )

    def get_active_grant(
        self,
        file_id: UUID,
        user_id: UUID,
    ) -> FileShare | None:
        return self._shares.get_active(
            file_id,
            user_id,
        )

    def resolve_accessible_file(
        self,
        user_id: UUID,
        file_id: UUID,
    ) -> tuple[StoredFile, FileShare | None]:
        """
        Return (file, grant) where grant is None for the owner.

        Raises ShareNotFoundError when the caller is neither the
        owner nor an active grantee (callers map this to 404 to
        avoid resource enumeration).
        """

        owned = self._files.get_for_user(
            user_id,
            file_id,
        )

        if owned is not None:
            return owned, None

        grant = self._shares.get_active(
            file_id,
            user_id,
        )

        if grant is None:
            raise ShareNotFoundError(
                "Stored file not found."
            )

        stored = self._files.get(file_id)

        if stored is None or stored.status != "active":
            raise ShareNotFoundError(
                "Stored file not found."
            )

        return stored, grant

    def session_key_for(
        self,
        user_id: UUID,
        stored: StoredFile,
        grant: FileShare | None,
    ) -> bytes:
        """
        Unwrap the AES session key for an owner (grant=None) or a
        grantee (grant set) using *their own* private key.
        """

        if grant is None:
            if stored.key_id is None:
                raise ShareError(
                    "File has no encryption key."
                )

            owner_key = self._keys.get_key(
                user_id,
                stored.key_id,
            )

            owner_private = self._keys.unlock_private_key(
                owner_key
            )

            owner_wrapped = self._read_owner_wrapped_key(
                stored
            )

            return self._hybrid.unwrap_key(
                owner_wrapped,
                owner_private,
            )

        # Grantee path: unwrap their per-grant copy with the key
        # recorded at share time. Fall back to their active key
        # only if the recorded key row is gone (SET NULL).
        raw = base64.b64decode(grant.wrapped_key)

        key_id = grant.grantee_key_id

        if key_id is not None:
            try:
                grantee_key = self._keys.get_key(
                    user_id,
                    key_id,
                )

                private = self._keys.unlock_private_key(
                    grantee_key
                )

                return self._hybrid.unwrap_key(
                    raw,
                    private,
                )
            except (KeyNotFoundError, Exception):
                # Fall through to active-key attempt so a
                # rotated-away key id still yields a clear
                # error below instead of a silent mismatch.
                pass

        active = self._keys.get_active_for_user(
            user_id
        )

        private = self._keys.unlock_private_key(
            active
        )

        return self._hybrid.unwrap_key(
            raw,
            private,
        )

    # -------------------------------------------------
    # Internals
    # -------------------------------------------------

    def _unwrap_owner_session_key(
        self,
        owner_id: UUID,
        stored: StoredFile,
    ) -> bytes:
        assert stored.key_id is not None

        try:
            owner_key = self._keys.get_key(
                owner_id,
                stored.key_id,
            )
        except KeyNotFoundError as exc:
            raise ShareError(
                "Owner encryption key not found."
            ) from exc

        try:
            owner_private = self._keys.unlock_private_key(
                owner_key
            )
        except Exception as exc:
            raise ShareError(
                f"Owner key is not usable for sharing: {exc}"
            ) from exc

        owner_wrapped = self._read_owner_wrapped_key(
            stored
        )

        try:
            return self._hybrid.unwrap_key(
                owner_wrapped,
                owner_private,
            )
        except Exception as exc:
            raise ShareError(
                f"Could not unwrap file session key: {exc}"
            ) from exc

    def _read_owner_wrapped_key(
        self,
        stored: StoredFile,
    ) -> bytes:
        if self._storage is None:
            raise ShareError(
                "Share service is not wired to storage."
            )

        container = self._storage.resolve_path(
            stored.storage_path
        )

        if not container.is_file():
            raise ShareError(
                "Encrypted container missing on disk."
            )

        stream, _, wrapped = self._serializer.open_file(
            container
        )

        try:
            return wrapped
        finally:
            if not stream.closed:
                stream.close()
