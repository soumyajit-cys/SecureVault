from app.crypto.aes.aes_gcm import (
    AESGCMCipher,
)


def test_encrypt_decrypt():

    cipher = AESGCMCipher()

    key = (
        cipher.generate_key()
    )

    plaintext = (
        b"SecureVault AES Test"
    )

    payload = (
        cipher.encrypt(
            plaintext,
            key,
        )
    )

    decrypted = (
        cipher.decrypt(
            payload,
            key,
        )
    )

    assert decrypted == plaintext