from __future__ import annotations

from contextlib import contextmanager
from typing import Any, BinaryIO, Iterable, Iterator

from botocore.exceptions import ClientError

from app.core.exceptions import NotFoundError
from app.infrastructure.storage.object_store import ObjectStore

_MIN_PART_BYTES = 5 * 1024 * 1024


def _validate_key(key: str) -> str:

    if not key or key.startswith("/") or ".." in key.split("/"):
        raise ValueError(f"Unsafe object key: {key!r}")

    return key


def _is_missing(exc: ClientError) -> bool:

    code = (exc.response.get("Error") or {}).get("Code", "")

    return code in ("404", "NoSuchKey", "NotFound", "NoSuchBucket")


class S3MultipartWriter:
    """
    Writable binary stream backed by an S3 multipart upload.

    Bytes are buffered until ``part_size`` (8 MiB by default)
    and uploaded part by part, so memory stays bounded no
    matter how large the object is. Closing the writer
    completes the upload; raising inside the ``with`` block
    aborts it, leaving no partial object behind.

    Part size must be >= 5 MiB (S3 minimum, except the last
    part) — enforced here so misconfiguration fails loudly.
    """

    def __init__(
        self,
        client: Any,
        bucket: str,
        key: str,
        part_size: int,
    ) -> None:

        if part_size < _MIN_PART_BYTES:
            raise ValueError(
                "Multipart part size must be at least 5 MiB."
            )

        self._client = client
        self._bucket = bucket
        self._key = key
        self._part_size = part_size

        response = client.create_multipart_upload(
            Bucket=bucket,
            Key=key,
        )

        self._upload_id: str = response["UploadId"]

        self._buffer = bytearray()

        self._parts: list[dict] = []

        self._part_number = 1

        self._closed = False

        self._bytes_written = 0

    # -- file-like API --------------------------------

    def write(self, data: bytes) -> int:

        if self._closed:
            raise ValueError("Writer is closed.")

        if not data:
            return 0

        self._buffer += data

        self._bytes_written += len(data)

        while len(self._buffer) >= self._part_size:
            self._upload_buffer(final=False)

        return len(data)

    def flush(self) -> None:

        return None

    @property
    def bytes_written(self) -> int:

        return self._bytes_written

    def close(self) -> None:

        if self._closed:
            return

        self._closed = True

        try:

            # Ship whatever is left as the final part (S3
            # allows the last part to be smaller than 5 MiB,
            # including a single-part or empty upload).
            self._upload_buffer(final=True)

            self._client.complete_multipart_upload(
                Bucket=self._bucket,
                Key=self._key,
                UploadId=self._upload_id,
                MultipartUpload={"Parts": self._parts},
            )

        except Exception:

            self.abort()

            raise

    def abort(self) -> None:

        try:

            self._client.abort_multipart_upload(
                Bucket=self._bucket,
                Key=self._key,
                UploadId=self._upload_id,
            )

        except Exception:

            pass

    # -- context manager ------------------------------

    def __enter__(self) -> S3MultipartWriter:

        return self

    def __exit__(self, exc_type, exc, tb) -> None:

        if exc_type is None:
            self.close()
        else:
            self._closed = True
            self.abort()

    # -- internals ------------------------------------

    def _upload_buffer(self, final: bool) -> None:

        if not final:
            # Called only when the buffer holds at least
            # one full part; ship exactly one part.
            data = bytes(self._buffer[: self._part_size])
            del self._buffer[: self._part_size]
        elif self._buffer:
            data = bytes(self._buffer)
            self._buffer.clear()
        elif self._parts:
            # Buffer already fully shipped as full-size
            # parts; nothing left for a final part.
            return
        else:
            # Zero-byte object: S3 still needs one part.
            data = b""

        # Non-final parts are always full-sized here; the
        # final part may be any size (including 0 bytes).
        response = self._client.upload_part(
            Bucket=self._bucket,
            Key=self._key,
            UploadId=self._upload_id,
            PartNumber=self._part_number,
            Body=data,
        )

        self._parts.append(
            {
                "ETag": response["ETag"],
                "PartNumber": self._part_number,
            }
        )

        self._part_number += 1


class S3Reader:
    """
    Readable binary stream over an S3 ``get_object`` body.

    Data is pulled from the network in ``read(n)`` sized
    chunks — the whole object is never buffered. Supports
    ``with`` blocks and iteration.
    """

    def __init__(
        self,
        body: Any,
    ) -> None:

        self._body = body

        self._closed = False

    def read(self, size: int = -1) -> bytes:

        if self._closed:
            raise ValueError("Reader is closed.")

        if size is None or size < 0:
            return self._body.read()

        return self._body.read(size) or b""

    def __iter__(self) -> Iterator[bytes]:

        while True:

            chunk = self.read(1024 * 1024)

            if not chunk:
                break

            yield chunk

    def close(self) -> None:

        if not self._closed:
            self._closed = True
            try:
                self._body.close()
            except Exception:
                pass

    def __enter__(self) -> S3Reader:

        return self

    def __exit__(self, exc_type, exc, tb) -> None:

        self.close()

    @property
    def closed(self) -> bool:

        return self._closed


class S3ObjectStore(ObjectStore):
    """
    ObjectStore over any S3-compatible API (AWS S3, Backblaze
    B2, MinIO, …) via boto3, configured with ``endpoint_url``
    so non-AWS endpoints work.

    Writes stream through multipart upload; reads stream
    through ranged/sequential ``get_object`` — memory stays
    flat for arbitrary object sizes.
    """

    def __init__(
        self,
        endpoint_url: str | None,
        bucket: str | None,
        access_key: str | None,
        secret_key: str | None,
        region: str = "us-west-004",
        part_size: int = 8 * 1024 * 1024,
    ) -> None:

        missing = [
            name
            for name, value in (
                ("S3_ENDPOINT_URL", endpoint_url),
                ("S3_BUCKET", bucket),
                ("S3_ACCESS_KEY", access_key),
                ("S3_SECRET_KEY", secret_key),
            )
            if not value
        ]

        if missing:
            raise RuntimeError(
                "S3 object storage misconfigured; missing: "
                + ", ".join(missing)
            )

        self.endpoint_url = endpoint_url
        self.bucket = bucket
        self.region = region
        self.part_size = part_size

        self._client_kwargs = {
            "endpoint_url": endpoint_url,
            "region_name": region,
            "aws_access_key_id": access_key,
            "aws_secret_access_key": secret_key,
        }

        self._client: Any | None = None

    # -------------------------------------------------
    # Client
    # -------------------------------------------------

    def _get_client(self) -> Any:

        if self._client is None:
            import boto3

            self._client = boto3.client(
                "s3",
                **self._client_kwargs,
            )

        return self._client

    # -------------------------------------------------
    # Writes
    # -------------------------------------------------

    @contextmanager
    def write(
        self,
        key: str,
    ) -> Iterator[BinaryIO]:

        _validate_key(key)

        writer = S3MultipartWriter(
            self._get_client(),
            self.bucket,  # type: ignore[arg-type]
            key,
            self.part_size,
        )

        with writer as stream:

            yield stream  # type: ignore[misc]

    # -------------------------------------------------
    # Reads
    # -------------------------------------------------

    def open(
        self,
        key: str,
        start: int = 0,
    ) -> BinaryIO:

        _validate_key(key)

        kwargs: dict = {"Bucket": self.bucket, "Key": key}

        if start > 0:
            kwargs["Range"] = f"bytes={start}-"

        try:

            response = self._get_client().get_object(**kwargs)

        except ClientError as exc:

            if _is_missing(exc):
                raise NotFoundError(
                    f"Object not found: {key}"
                ) from exc

            raise

        return S3Reader(response["Body"])  # type: ignore[return-value]

    def exists(
        self,
        key: str,
    ) -> bool:

        _validate_key(key)

        try:

            self._get_client().head_object(
                Bucket=self.bucket,
                Key=key,
            )

        except ClientError as exc:

            if _is_missing(exc):
                return False

            raise

        return True

    def size(
        self,
        key: str,
    ) -> int | None:

        _validate_key(key)

        try:

            response = self._get_client().head_object(
                Bucket=self.bucket,
                Key=key,
            )

        except ClientError as exc:

            if _is_missing(exc):
                return None

            raise

        return int(response.get("ContentLength", 0))

    # -------------------------------------------------
    # Delete / list
    # -------------------------------------------------

    def delete(
        self,
        key: str,
    ) -> bool:

        _validate_key(key)

        if not self.exists(key):
            return False

        self._get_client().delete_object(
            Bucket=self.bucket,
            Key=key,
        )

        return True

    def iter_keys(
        self,
        prefix: str = "",
    ) -> Iterable[str]:

        paginator = self._get_client().get_paginator(
            "list_objects_v2"
        )

        for page in paginator.paginate(
            Bucket=self.bucket,
            Prefix=prefix,
        ):

            for obj in page.get("Contents", []):

                yield obj["Key"]
