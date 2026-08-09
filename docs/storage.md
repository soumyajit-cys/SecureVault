# SecureVault — Storage

## Vault layout

`STORAGE_DIR` (default `backend/storage/`) hosts:

- `containers/` — encrypted SecureVault containers, one file per vault item,
  organized under per-user directories derived from UUIDs (never from user
  input), so path traversal is impossible by construction.
- `temp/` — staging area for uploads and decryption; swept by the garbage
  collector (`TEMP_FILE_MAX_AGE_HOURS`).
- `folder-unpack/` — staging for folder archive extraction.

`StorageService.resolve_path` additionally performs a resolved-path
containment check (`Path.resolve().is_relative_to(root)`); anything outside
the root is rejected.

## Upload

1. `POST /files/upload` (multipart) streams the file to a temp path while
   enforcing `MAX_UPLOAD_SIZE_BYTES` (413 when exceeded).
2. The file is stream-encrypted into a SecureVault container (see
   `docs/cryptography.md`), writing to a staging container path.
3. On success the container is atomically moved into the vault layout and a
   `StoredFile` metadata row is created (sizes, SHA-256, mime, key id,
   optional idempotency key).
4. Failure at any step removes temp and staging files; incomplete uploads
   cannot leave records or orphan containers behind.

Idempotent uploads: sending the same `X-Idempotency-Key` (8–64 chars)
replays the previous result instead of duplicating storage.

Folder uploads accept a ZIP, extract it with traversal/duplicate/zip-bomb
guards, archive it again into the encrypted container with `folder_archiver`.

## Download

`GET /files/{id}/download`:

1. Resolves the file row scoped to the caller (404 otherwise).
2. Streams the container, validates the header, unwraps the session key,
   stream-decrypts, computes SHA-256 and compares with stored metadata.
3. Returns the plaintext with the original filename/mime (filename comes
   from metadata, never from the container).

Failure modes: wrong key, corrupted ciphertext/nonce/tag/header/truncation
all fail closed with a generic error and no partial output.

## Soft delete, restore, GC

- `DELETE /files/{id}` soft-deletes (status + `deleted_at`), keeping the
  container for a grace period.
- `POST /folders/{id}/restore` decrypts and re-archives a folder container
  with the same safety checks as upload.
- `GarbageCollector`:
  - collects orphan containers (no metadata row),
  - removes metadata rows without containers,
  - purges soft-deleted files past retention,
  - sweeps temp files older than `TEMP_FILE_MAX_AGE_HOURS`.
- Triggered manually via `POST /admin/garbage-collect` and optionally on a
  background interval (`GARBAGE_COLLECTION_ENABLED` +
  `GARBAGE_COLLECTION_INTERVAL_HOURS`).

## Quotas

`QuotaService` tracks per-user stored+deleted bytes; uploads exceeding the
quota are rejected (413). Admins may adjust quotas.

## Security properties

- Ownership-scoped queries everywhere (`user_id` filter).
- No user-controlled filenames or paths touch the filesystem; only
  metadata stores the original name.
- Symlink-free writes; containers are moved, not written in place.
- Temp files are UUID-named and unlinked on failure paths.
