from __future__ import annotations

from cryptography.exceptions import InvalidKey

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives import serialization

from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.asymmetric import rsa
from app.crypto.models.key_pair import RSAKeyPair

from app.crypto.exceptions import (
    DecryptionError,
    EncryptionError,
    InvalidKeyError,
)


class RSAService:

    KEY_SIZE = 4096

    PUBLIC_EXPONENT = 65537

    HASH = hashes.SHA256()

    def generate_key_pair(
        self,
    ) -> tuple[rsa.RSAPrivateKey, rsa.RSAPublicKey]:

        private_key = rsa.generate_private_key(
            public_exponent=self.PUBLIC_EXPONENT,
            key_size=self.KEY_SIZE,
        )

        public_key = private_key.public_key()

        return private_key, public_key

    def serialize_public_key(
        self,
        public_key: rsa.RSAPublicKey,
    ) -> bytes:

        return public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )

    def serialize_private_key(
        self,
        private_key: rsa.RSAPrivateKey,
        password: str | None = None,
    ) -> bytes:

        if password:

            algorithm = serialization.BestAvailableEncryption(
                password.encode()
            )

        else:

            algorithm = serialization.NoEncryption()

        return private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=algorithm,
        )

    def load_public_key(
        self,
        pem: bytes,
    ) -> rsa.RSAPublicKey:

        try:

            key = serialization.load_pem_public_key(
                pem,
            )

            if not isinstance(
                key,
                rsa.RSAPublicKey,
            ):
                raise InvalidKeyError(
                    "Invalid RSA public key."
                )

            return key

        except (
            ValueError,
            TypeError,
            InvalidKey,
        ) as exc:

            raise InvalidKeyError(
                str(exc)
            ) from exc

    def load_private_key(
        self,
        pem: bytes,
        password: str | None = None,
    ) -> rsa.RSAPrivateKey:

        try:

            key = serialization.load_pem_private_key(
                pem,
                password=password.encode()
                if password
                else None,
            )

            if not isinstance(
                key,
                rsa.RSAPrivateKey,
            ):
                raise InvalidKeyError(
                    "Invalid RSA private key."
                )

            return key

        except (
            ValueError,
            TypeError,
            InvalidKey,
        ) as exc:

            raise InvalidKeyError(
                str(exc)
            ) from exc

    def encrypt(
        self,
        plaintext: bytes,
        public_key: rsa.RSAPublicKey,
    ) -> bytes:

        try:

            return public_key.encrypt(
                plaintext,
                padding.OAEP(
                    mgf=padding.MGF1(
                        algorithm=self.HASH,
                    ),
                    algorithm=self.HASH,
                    label=None,
                ),
            )

        except Exception as exc:

            raise EncryptionError(
                str(exc)
            ) from exc

    def decrypt(
        self,
        ciphertext: bytes,
        private_key: rsa.RSAPrivateKey,
    ) -> bytes:

        try:

            return private_key.decrypt(
                ciphertext,
                padding.OAEP(
                    mgf=padding.MGF1(
                        algorithm=self.HASH,
                    ),
                    algorithm=self.HASH,
                    label=None,
                ),
            )

        except Exception as exc:

            raise DecryptionError(
                str(exc)
            ) from exc

    def fingerprint(
        self,
        public_key: rsa.RSAPublicKey,
    ) -> str:

        pem = self.serialize_public_key(
            public_key
        )

        digest = hashes.Hash(
            hashes.SHA256(),
        )

        digest.update(
            pem,
        )

        return digest.finalize().hex()