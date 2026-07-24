from __future__ import annotations

from cryptography.hazmat.primitives.asymmetric.rsa import (
    RSAPrivateKey,
    RSAPublicKey,
)

from pydantic import BaseModel
from pydantic import ConfigDict


class RSAKeyPair(BaseModel):

    model_config = ConfigDict(
        arbitrary_types_allowed=True
    )

    private_key: RSAPrivateKey

    public_key: RSAPublicKey