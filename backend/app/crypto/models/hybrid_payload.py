from pydantic import BaseModel


class HybridEncryptedPayload(BaseModel):
    encrypted_key: str
    nonce: str
    ciphertext: str
    tag: str

    symmetric_algorithm: str = "AES-256-GCM"
    asymmetric_algorithm: str = "RSA-4096-OAEP-SHA256"