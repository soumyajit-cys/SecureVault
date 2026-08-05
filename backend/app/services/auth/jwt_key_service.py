from datetime import UTC
from datetime import datetime
from datetime import timedelta
import secrets

import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from app.core.at_rest import (
    EncryptedSecret,
    decrypt_secret,
    encrypt_secret,
)
from app.core.config import get_settings
from app.core.exceptions import InvalidTokenError
from app.core.exceptions import TokenExpiredError
from app.domain.models.jwt_signing_key import JwtSigningKey

settings = get_settings()


class JwtKeyService:

    def __init__(
        self,
        repository,
    ):
        self.repository = repository
        self._cache: dict[str, JwtSigningKey] = {}

    def ensure_active_key(
        self,
    ) -> JwtSigningKey:
        """
        Return the current active signing key; create
        one if none exists yet (first startup).
        """

        active = self.repository.get_active()

        if active is None:
            active = self._generate_and_store()

        return active

    def rotate(self) -> JwtSigningKey:
        """
        Retire the current active key and mint a fresh
        one. Old keys stay available for verification
        within the grace period so sessions do not break.
        """

        now = datetime.now(UTC)

        active = self.repository.get_active()

        if active is not None:
            self.repository.retire(active, now)

        self._cache.clear()

        return self._generate_and_store()

    def rotate_if_due(self) -> JwtSigningKey:
        """
        Rotate when the active key is older than the
        configured interval. No-op if the key is fresh.
        """

        now = datetime.now(UTC)

        active = (
            self.repository
            .get_active()
        )

        if active is None:
            return self.ensure_active_key()

        created_at = active.created_at

        if created_at.tzinfo is None:
            created_at = created_at.replace(
                tzinfo=UTC
            )

        age = now - created_at

        if (
            age
            >= timedelta(
                days=settings.JWT_KEY_ROTATION_DAYS
            )
        ):
            return self.rotate()

        return active

    def sign(
        self,
        claims: dict,
        expires_delta: timedelta,
    ) -> str:

        key = self.rotate_if_due()

        payload = claims.copy()

        payload["exp"] = (
            datetime.now(UTC)
            + expires_delta
        )

        private_key = (
            serialization.load_pem_private_key(
                self._private_key_pem(key).encode(),
                password=None,
            )
        )

        return jwt.encode(
            payload,
            private_key,
            algorithm=key.algorithm,
            headers={
                "kid": key.key_id,
            },
        )

    def decode(
        self,
        token: str,
    ) -> dict:

        try:

            kid = (
                jwt.get_unverified_header(token)
                .get("kid")
            )

        except jwt.InvalidTokenError:
            raise InvalidTokenError(
                "Invalid token"
            )

        key = self._resolve_key(kid)

        if key is None:
            raise InvalidTokenError(
                "Signing key not found"
            )

        if (
            key.status == "retired"
            and self._is_beyond_grace(
                key.retired_at
            )
        ):
            raise InvalidTokenError(
                "Signing key retired"
            )

        try:

            payload = jwt.decode(
                token,
                key.public_key_pem.encode(),
                algorithms=[key.algorithm],
                leeway=settings.JWT_LEEWAY_SECONDS,
            )

        except jwt.ExpiredSignatureError:
            raise TokenExpiredError(
                "Token expired"
            )

        except jwt.InvalidTokenError:
            raise InvalidTokenError(
                "Invalid token"
            )

        return payload

    def _resolve_key(
        self,
        kid: str | None,
    ) -> JwtSigningKey | None:

        if kid and kid in self._cache:
            return self._cache[kid]

        if kid:
            entry = (
                self.repository
                .get_by_key_id(kid)
            )

            if entry is not None:
                self._cache[kid] = entry
                return entry

        return None

    def _is_beyond_grace(
        self,
        retired_at: datetime | None,
    ) -> bool:

        if retired_at is None:
            return False

        if retired_at.tzinfo is None:
            retired_at = retired_at.replace(
                tzinfo=UTC
            )

        return (
            retired_at
            + timedelta(
                days=settings.JWT_RETIRED_KEY_GRACE_DAYS
            )
        ) < datetime.now(UTC)

    def _private_key_pem(
        self,
        key: JwtSigningKey,
    ) -> str:
        """
        Return the signing private key in PEM form.

        New keys carry the private material as an AES-256-GCM
        envelope at rest; legacy rows created before encryption
        keep a plaintext PEM that is still readable.
        """

        if key.has_encrypted_private_key:

            secret = EncryptedSecret(
                ciphertext=key.encrypted_private_key_pem,
                nonce=key.private_key_nonce,
                tag=key.private_key_tag,
                salt=key.private_key_salt,
            )

            return (
                decrypt_secret(secret)
                .decode()
            )

        if key.private_key_pem:
            return key.private_key_pem

        raise InvalidTokenError(
            "Signing key material is missing"
        )

    def _generate_and_store(
        self,
    ) -> JwtSigningKey:

        key_id = (
            f"sv-"
            f"{secrets.token_urlsafe(6)}"
        )

        private_pem, public_pem = (
            self._mint_key_pair()
        )

        envelope = encrypt_secret(
            private_pem.encode()
        )

        entry = JwtSigningKey(
            key_id=key_id,
            algorithm="RS256",
            status="active",
            private_key_pem=None,
            encrypted_private_key_pem=(
                envelope.ciphertext
            ),
            private_key_nonce=envelope.nonce,
            private_key_tag=envelope.tag,
            private_key_salt=envelope.salt,
            public_key_pem=public_pem,
        )

        return self.repository.create(entry)

    def _mint_key_pair(
        self,
    ) -> tuple[str, str]:

        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=4096,
        )

        private_pem = (
            private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=(
                    serialization.NoEncryption()
                ),
            )
        )

        public_pem = (
            private_key.public_key()
            .public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo,
            )
        )

        return (
            private_pem.decode(),
            public_pem.decode(),
        )