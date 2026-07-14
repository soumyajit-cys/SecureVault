import hashlib
import secrets


def generate_token_family():
    return secrets.token_hex(
        32
    )


def generate_session_id():
    return secrets.token_hex(
        32
    )


def hash_token(
    token: str
):
    return hashlib.sha256(
        token.encode()
    ).hexdigest()