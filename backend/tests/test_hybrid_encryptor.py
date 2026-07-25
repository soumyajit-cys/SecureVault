from app.crypto.rsa.hybrid_encryptor import (
    HybridEncryptor,
)

from app.crypto.rsa.rsa_service import (
    RSAService,
)


def test_hybrid_encrypt_decrypt():

    rsa = RSAService()

    keypair = rsa.generate_key_pair()

    encryptor = HybridEncryptor()

    plaintext = (
        b"SecureVault Hybrid Encryption"
    )

    payload = encryptor.encrypt(
        plaintext,
        keypair.public_key,
    )

    decrypted = encryptor.decrypt(
        payload,
        keypair.private_key,
    )

    assert decrypted == plaintext