from fastapi import Depends

from app.api.dependencies.storage import (
    get_crypto_service,
)

__all__ = [
    "get_crypto_service",
]