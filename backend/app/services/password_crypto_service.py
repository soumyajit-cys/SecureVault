from app.crypto.argon2.kdf import (
    Argon2KDF,
)

from app.crypto.aes.aes_gcm import (
    AESGCMCipher,
)


class PasswordCryptoService:

    def __init__(
        self,
    ):
        self.kdf = Argon2KDF()

        self.cipher = AESGCMCipher()

    def encrypt(
        self,
        plaintext: str,
        password: str,
    ):

        key, salt = (
            self.kdf
            .derive_key_with_new_salt(
                password
            )
        )

        payload = (
            self.cipher.encrypt(
                plaintext.encode(),
                key,
            )
        )

        return {
            "salt": salt.hex(),
            "payload": payload,
        }

    def decrypt(
        self,
        payload,
        password: str,
        salt_hex: str,
    ):

        key = (
            self.kdf.derive_key(
                password,
                bytes.fromhex(
                    salt_hex
                ),
            )
        )

        decrypted = (
            self.cipher.decrypt(
                payload,
                key,
            )
        )

        return decrypted.decode()