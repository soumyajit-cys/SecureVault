import secrets


def generate_secret(length: int = 64) -> str:
    return secrets.token_urlsafe(length)


