from app.infrastructure.storage.factory import (
    build_object_store,
)
from app.infrastructure.storage.keys import (
    validate_container_key,
)
from app.infrastructure.storage.local_store import (
    LocalObjectStore,
)
from app.infrastructure.storage.object_store import (
    ObjectStore,
    closing_reader,
)

try:  # boto3 is required only for the "s3" backend
    from app.infrastructure.storage.s3_store import (
        S3MultipartWriter,
        S3ObjectStore,
        S3Reader,
    )
except ImportError:  # pragma: no cover
    S3MultipartWriter = None  # type: ignore[assignment]
    S3ObjectStore = None  # type: ignore[assignment]
    S3Reader = None  # type: ignore[assignment]

__all__ = [
    "ObjectStore",
    "LocalObjectStore",
    "S3ObjectStore",
    "S3MultipartWriter",
    "S3Reader",
    "build_object_store",
    "closing_reader",
    "validate_container_key",
]
