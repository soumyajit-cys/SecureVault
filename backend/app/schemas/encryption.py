from pydantic import BaseModel


class EncryptTextRequest(
    BaseModel
):
    plaintext: str


class DecryptTextRequest(
    BaseModel
):
    nonce: str

    ciphertext: str

    tag: str