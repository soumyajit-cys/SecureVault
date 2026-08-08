"""
Purpose-scoped key material.

A single root key (MASTER_ENCRYPTION_KEY, falling
back to SECRET_KEY for existing deployments) feeds
HKDF-SHA256 derivations. Each purpose in the app
uses its own info label, so a sub-key for one domain
can never be substituted in another even when the
root material is identical.
"""

from __future__ import annotations

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

from app.core.config import get_settings

# Purpose labels - never rename or reuse these for a
# different domain, or every wrapped secret breaks.
PURPOSE_AT_REST = b"securevault-key-material:at-rest-v1"
PURPOSE_PRIVATE_KEY_WRAP = b"securevault-key-material:private-key-wrap-v1"


def root_key_material() -> bytes:
    """
    Raw bytes used as HKDF input key material.

    MASTER_ENCRYPTION_KEY is preferred; deployments
    that predate it keep using SECRET_KEY so existing
    envelopes remain decryptable.
    """

    settings = get_settings()

    master = (
        settings.MASTER_ENCRYPTION_KEY
        or settings.SECRET_KEY
    )

    return master.encode()


def derive_key_material(
    purpose: bytes,
    salt: bytes,
    length: int = 32,
) -> bytes:
    """
    Derive a purpose-scoped sub-key.

    Args:
        purpose: domain-separation label. Must be one
            of the module PURPOSE_* constants.
        salt: per-object random salt.
        length: output key length in bytes.

    Returns:
        Deterministic sub-key for the given purpose
        and salt under the root key material.
    """

    hkdf = HKDF(
        algorithm=hashes.SHA256(),
        length=length,
        salt=salt,
        info=purpose,
    )

    return hkdf.derive(
        root_key_material()
    )
