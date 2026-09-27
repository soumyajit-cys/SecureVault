from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from app.infrastructure.storage.local_store import LocalObjectStore
from app.infrastructure.storage.object_store import ObjectStore

if TYPE_CHECKING:  # pragma: no cover
    from app.core.config import Settings


def build_object_store(
    settings=None,
    *,
    root: str | Path | None = None,
    backend: str | None = None,
) -> ObjectStore:
    """
    Return the committed-container store selected by settings.

    - ``STORAGE_BACKEND="local"`` (default): files under
      ``<STORAGE_DIR>/files`` — the historical behavior.
    - ``STORAGE_BACKEND="s3"``: any S3-compatible bucket
      (Backblaze B2, AWS S3, MinIO) via boto3.

    Pass an explicit ``root`` in tests to isolate the local
    store; pass ``settings`` explicitly to avoid the cached
    global (tests that mutate env vars).
    """

    from app.core.config import get_settings

    resolved: Settings = settings or get_settings()

    selected = (
        backend or resolved.STORAGE_BACKEND or "local"
    ).lower()

    if selected == "s3":
        from app.infrastructure.storage.s3_store import (
            S3ObjectStore,
        )

        return S3ObjectStore(
            endpoint_url=resolved.S3_ENDPOINT_URL,
            bucket=resolved.S3_BUCKET,
            access_key=resolved.S3_ACCESS_KEY,
            secret_key=resolved.S3_SECRET_KEY,
            region=resolved.S3_REGION,
            part_size=resolved.S3_MULTIPART_PART_BYTES,
        )

    if selected != "local":
        raise RuntimeError(
            "STORAGE_BACKEND must be 'local' or 's3', "
            f"got {resolved.STORAGE_BACKEND!r}."
        )

    return LocalObjectStore(
        root or Path(resolved.STORAGE_DIR)
    )
