from pydantic import BaseModel
from pydantic import Field

MAX_TEXT_PLAINTEXT_BYTES = 1024 * 1024  # 1 MiB

MAX_ENCRYPTED_FIELD_BYTES = 2 * 1024 * 1024  # 2 MiB

MAX_AAD_BYTES = 4096


class EncryptTextRequest(
    BaseModel
):
    plaintext: str = Field(
        max_length=MAX_TEXT_PLAINTEXT_BYTES,
    )

    aad: str | None = Field(
        default=None,
        max_length=MAX_AAD_BYTES,
    )


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
    nonce: str = Field(
        max_length=MAX_ENCRYPTED_FIELD_BYTES,
    )

    ciphertext: str = Field(
        max_length=MAX_ENCRYPTED_FIELD_BYTES,
    )

    tag: str = Field(
        max_length=MAX_ENCRYPTED_FIELD_BYTES,
    )

    encrypted_key: str = Field(
        max_length=MAX_ENCRYPTED_FIELD_BYTES,
    )


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