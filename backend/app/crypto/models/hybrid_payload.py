from __future__ import annotations

from pydantic import BaseModel, Field


class HybridEncryptedPayload(BaseModel):
    """
    Represents the complete output of hybrid encryption.

    The AES key is encrypted using RSA-OAEP.
    The payload itself is encrypted using AES-256-GCM.
    """

    encrypted_key: bytes = Field(
        description="RSA encrypted AES-256 key."
    )

    nonce: bytes = Field(
        description="AES-GCM nonce."
    )

    ciphertext: bytes = Field(
        description="Encrypted payload."
    )

    tag: bytes = Field(
        description="AES-GCM authentication tag."
    )

    algorithm: str = "AES-256-GCM"

    key_algorithm: str = "RSA-4096-OAEP"

    hash_algorithm: str = "SHA-256"

    version: int = 1