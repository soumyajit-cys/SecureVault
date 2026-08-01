from cryptography.hazmat.primitives.asymmetric.rsa import (
    RSAPrivateKey,
    RSAPublicKey,
)

from app.crypto.exceptions import (
    DecryptionError,
    InvalidKeyError,
)

from app.crypto.rsa.rsa_service import RSAService


def test_generate_key_pair():

    service = RSAService()

    keypair = (
        service.generate_key_pair()
    )

    assert isinstance(
        keypair.private_key,
        RSAPrivateKey,
    )

    assert isinstance(
        keypair.public_key,
        RSAPublicKey,
    )


def test_public_key_serialization():

    service = RSAService()

    keypair = (
        service.generate_key_pair()
    )

    pem = service.serialize_public_key(
        keypair.public_key
    )

    loaded = service.load_public_key(
        pem
    )

    assert isinstance(
        loaded,
        RSAPublicKey,
    )


def test_private_key_serialization_without_password():

    service = RSAService()

    keypair = (
        service.generate_key_pair()
    )

    pem = service.serialize_private_key(
        keypair.private_key
    )

    loaded = service.load_private_key(
        pem
    )

    assert isinstance(
        loaded,
        RSAPrivateKey,
    )


def test_private_key_serialization_with_password():

    service = RSAService()

    keypair = (
        service.generate_key_pair()
    )

    pem = service.serialize_private_key(
        keypair.private_key,
        password="SecureVaultPassword123!",
    )

    loaded = service.load_private_key(
        pem,
        password="SecureVaultPassword123!",
    )

    assert isinstance(
        loaded,
        RSAPrivateKey,
    )


def test_encrypt_decrypt():

    service = RSAService()

    keypair = (
        service.generate_key_pair()
    )

    plaintext = (
        b"SecureVault RSA Encryption"
    )

    ciphertext = service.encrypt(
        plaintext,
        keypair.public_key,
    )

    decrypted = service.decrypt(
        ciphertext,
        keypair.private_key,
    )

    assert decrypted == plaintext


def test_public_key_fingerprint():

    service = RSAService()

    keypair = (
        service.generate_key_pair()
    )

    fingerprint = (
        service.fingerprint(
            keypair.public_key
        )
    )

    assert len(
        fingerprint
    ) == 64


def test_invalid_public_key():

    service = RSAService()

    invalid = (
        b"-----BEGIN PUBLIC KEY-----\n"
        b"INVALID\n"
        b"-----END PUBLIC KEY-----"
    )

    try:

        service.load_public_key(
            invalid
        )

        assert False

    except InvalidKeyError:

        assert True


def test_invalid_private_key():

    service = RSAService()

    invalid = (
        b"-----BEGIN PRIVATE KEY-----\n"
        b"INVALID\n"
        b"-----END PRIVATE KEY-----"
    )

    try:

        service.load_private_key(
            invalid
        )

        assert False

    except InvalidKeyError:

        assert True


def test_decrypt_with_wrong_private_key():

    service = RSAService()

    keypair_a = (
        service.generate_key_pair()
    )

    keypair_b = (
        service.generate_key_pair()
    )

    ciphertext = service.encrypt(
        b"SecureVault",
        keypair_a.public_key,
    )

    try:

        service.decrypt(
            ciphertext,
            keypair_b.private_key,
        )

        assert False

    except DecryptionError:

        assert True
