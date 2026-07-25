from pydantic import BaseModel
from pydantic import ConfigDict


class EncryptedData(BaseModel):

    model_config = ConfigDict(
        arbitrary_types_allowed=True
    )

    nonce: bytes

    ciphertext: bytes

    tag: bytes