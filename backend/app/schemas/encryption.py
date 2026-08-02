from pydantic import BaseModel


class EncryptTextRequest(
    BaseModel
):
    plaintext: str


class EncryptTextResponse(
    BaseModel
):
    nonce: str

    ciphertext: str

    tag: str

    encrypted_key: str

    algorithm: str

    key_algorithm: str

    hash_algorithm: str


class DecryptTextRequest(
    BaseModel
):
    nonce: str

    ciphertext: str

    tag: str

    encrypted_key: str


class DecryptTextResponse(
    BaseModel
):
    plaintext: str


class EncryptFileResponse(BaseModel):
    file_id: str

    filename: str

    original_size: int

    encrypted_size: int

    sha256: str

    is_folder: bool

    created_at: str