from pydantic import BaseModel


class EncryptedPayload(
    BaseModel
):
    nonce: str

    ciphertext: str

    tag: str

    algorithm: str = (
        "AES-256-GCM"
    )