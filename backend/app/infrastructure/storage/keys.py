from __future__ import annotations

import re
import uuid

# Every committed container key is derived server-side by
# StorageService.container_key() as:
#
#     files/<user_id>/<file_id>.svlt
#
# Nothing user-controlled ever flows into a key. This pattern
# pins that shape so a malicious or corrupted
# StoredFile.storage_path DB value cannot escape the container
# namespace or collide with another key family:
#
# - no ``..`` segments, no absolute keys (prefix escape);
# - no foreign prefixes (``tmp/…``, ``vault/…``, bare names);
# - both path segments must be UUID-shaped, so one user cannot
#   address a free-form key belonging to another user.
#
# Ownership itself is enforced one layer up, at the database:
# repositories scope rows by owner (``get_for_user``) and share
# grants are validated before grantee reads. A user-id match is
# deliberately NOT asserted here — share-grantee downloads
# legitimately open containers whose key embeds the *owner's*
# user id, so such a check would break sharing.
_CONTAINER_KEY_RE = re.compile(
    r"^files/"
    r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-"
    r"[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-"
    r"[0-9a-fA-F]{12}/"
    r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-"
    r"[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-"
    r"[0-9a-fA-F]{12}\.svlt$"
)


def validate_container_key(key: str) -> str:
    """
    Enforce the container-key shape invariant.

    Returns the key unchanged when it matches
    ``files/<uuid>/<uuid>.svlt``; raises ValueError otherwise.
    This is a fail-loud contract check for corrupted DB values
    or programming errors — it is not user-input validation,
    because keys are never built from user input.
    """

    if not isinstance(key, str) or not _CONTAINER_KEY_RE.match(key):
        raise ValueError(
            f"Refusing unsafe container key: {key!r}. "
            "Expected 'files/<user-uuid>/<file-uuid>.svlt'."
        )

    # Belt and braces: the regex pins hex+hyphens, but parsing
    # as UUIDs guarantees canonical shape, not just length.
    try:
        _, user_part, file_part = key.split("/")
        uuid.UUID(user_part)
        uuid.UUID(file_part.removesuffix(".svlt"))
    except (ValueError, AttributeError) as exc:
        raise ValueError(
            f"Refusing unsafe container key: {key!r}."
        ) from exc

    return key
