from app.crypto.rsa.hybrid_encryptor import (
    HybridEncryptor,
)
from app.crypto.rsa.rsa_service import (
    RSAService,
)


def test_wrap_unwrap_key():

    rsa = RSAService()

    keypair = rsa.generate_key_pair()

    hybrid = HybridEncryptor()

    session_key = hybrid.generate_session_key()

    wrapped = hybrid.wrap_key(
        session_key,
        keypair.public_key,
    )

    recovered = hybrid.unwrap_key(
        wrapped,
        keypair.private_key,
    )

    assert recovered == session_key