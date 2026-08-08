import pytest

from app.core.key_material import (
    PURPOSE_AT_REST,
    PURPOSE_PRIVATE_KEY_WRAP,
    derive_key_material,
    root_key_material,
)
from app.core.at_rest import (
    EncryptedSecret,
    decrypt_secret,
    encrypt_secret,
)


class TestPurposeScopedKeyMaterial:
    def test_root_material_is_bytes(self):
        material = root_key_material()

        assert isinstance(material, bytes)
        assert len(material) > 0

    def test_same_purpose_and_salt_is_deterministic(self):
        salt = b"fixed-salt-value"

        first = derive_key_material(
            PURPOSE_AT_REST,
            salt,
        )

        second = derive_key_material(
            PURPOSE_AT_REST,
            salt,
        )

        assert first == second
        assert len(first) == 32

    def test_different_purposes_diverge(
        self,
    ):
        salt = b"fixed-salt-value"

        at_rest = derive_key_material(
            PURPOSE_AT_REST,
            salt,
        )

        key_wrap = derive_key_material(
            PURPOSE_PRIVATE_KEY_WRAP,
            salt,
        )

        assert at_rest != key_wrap

    def test_different_salts_diverge(self):
        at_rest_a = derive_key_material(
            PURPOSE_AT_REST,
            b"salt-a",
        )

        at_rest_b = derive_key_material(
            PURPOSE_AT_REST,
            b"salt-b",
        )

        assert at_rest_a != at_rest_b

    def test_at_rest_round_trip(
        self,
    ):
        """
        Secrets wrapped under the purpose-scoped
        derivation decrypt with the same machinery the
        services use at runtime.
        """

        secret = encrypt_secret(
            b"sensitive-material"
        )

        assert isinstance(secret, EncryptedSecret)

        assert secret.is_set()

        plaintext = decrypt_secret(secret)

        assert plaintext == b"sensitive-material"

    def test_envelope_survives_purpose_rename(
        self,
    ):
        """
        The info label doubles as the purpose, so a
        secret encrypted with an explicit (older)
        label still decrypts via the default path.
        """

        secret = encrypt_secret(
            b"legacy-data",
            info_label=PURPOSE_AT_REST,
        )

        assert (
            decrypt_secret(secret)
            == b"legacy-data"
        )
