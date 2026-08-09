# SecureVault — API Reference

Base path: `/api/v1`. Interactive docs: `/docs` (OpenAPI).

All endpoints except auth/health require `Authorization: Bearer <access_token>`.
Standard error envelope: `{"detail": "..."}` with appropriate HTTP status
(401 auth, 403 permission, 404 missing/not-owned, 409 conflict, 413 too
large, 422 validation, 429 rate limited).

## Health & operations

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/health` | liveness summary |
| GET | `/health/live` | liveness (no dependencies) |
| GET | `/health/ready` | readiness (verifies DB connectivity) |
| GET | `/metrics` | Prometheus-format metrics |

## Auth

| Method | Path | Notes |
| --- | --- | --- |
| POST | `/auth/register` | email, username, password |
| POST | `/auth/login` | `mfa_required` + `mfa_token` when TOTP enabled |
| POST | `/auth/mfa/verify` | mfa_token + TOTP/recovery code → tokens |
| POST | `/auth/refresh` | rotating refresh token |
| POST | `/auth/logout` | revokes refresh token |
| POST | `/auth/change-password` | revokes other sessions |
| GET | `/auth/mfa/status` | enabled? |
| POST | `/auth/mfa/setup` | new TOTP secret |
| POST | `/auth/mfa/enable` | secret + code |
| POST | `/auth/mfa/disable` | code required |
| POST | `/auth/passkeys/register/begin` | FIDO2 challenge |
| POST | `/auth/passkeys/register/complete` | attestation → credential |
| GET | `/auth/passkeys` | list credentials |
| DELETE | `/auth/passkeys/{id}` | remove credential |
| POST | `/auth/passkeys/login/begin` | assertion challenge |
| POST | `/auth/passkeys/login/complete` | assertion → tokens |
| POST | `/auth/password-reset/request` | unenumeration-safe |
| POST | `/auth/password-reset/confirm` | token + new password |
| POST | `/auth/verify-email` | token |
| POST | `/auth/resend-verification` | new email token |
| GET | `/auth/sessions` | active sessions |
| DELETE | `/auth/sessions/{id}` | revoke one session |
| POST | `/auth/sessions/revoke-all` | revoke others |

## Profile

| Method | Path | Notes |
| --- | --- | --- |
| GET | `/profile/me` | own profile |

## Encryption (text)

| Method | Path | Notes |
| --- | --- | --- |
| POST | `/encryption/text/encrypt` | plaintext (≤1 MiB), optional `aad` (≤4 KiB) |
| POST | `/encryption/text/decrypt` | nonce/ciphertext/tag/encrypted_key (+ same `aad` if used) |

## Files

| Method | Path | Notes |
| --- | --- | --- |
| POST | `/files/upload` | multipart `upload`; optional `X-Idempotency-Key`; size-capped |
| GET | `/files` | pagination, `status`, `mime_type`, `is_folder`, `search` |
| GET | `/files/summary` | storage summary per user |
| GET | `/files/{id}` | metadata |
| GET | `/files/{id}/download` | stream-decrypted original |
| PATCH | `/files/{id}` | rename, restore |
| DELETE | `/files/{id}` | soft delete |

## Folders

| Method | Path | Notes |
| --- | --- | --- |
| POST | `/folders/upload` | multipart ZIP; archive safety checks |
| GET | `/folders` | list folder containers |
| POST | `/folders/{id}/restore` | decrypt + re-archive |

## Keys

| Method | Path | Notes |
| --- | --- | --- |
| POST | `/keys` | generate (name, validity_days) → 201 |
| GET | `/keys` | list, filter by status |
| GET | `/keys/active` | current active key |
| GET | `/keys/{id}` | detail |
| POST | `/keys/rotate` | current_key_id → new key; old revoked |
| POST | `/keys/{id}/revoke` | revoke |

Key operations are ownership-scoped: another user's key returns 404.

## Audit

| Method | Path | Notes |
| --- | --- | --- |
| GET | `/audit/logs` | own events, paginated |
| GET | `/audit/admin/logs` | all events (admin) |
| GET | `/audit/export` | CSV export (Auditor+) |

## Admin

| Method | Path | Notes |
| --- | --- | --- |
| GET | `/admin/status` | system status |
| GET | `/admin/users` | list users |
| POST | `/admin/users/{id}/activate|deactivate` | user lifecycle |
| POST | `/admin/users` | create user (admin) |
| PATCH | `/admin/users/{id}` | update user |
| DELETE | `/admin/users/{id}` | delete user (self-delete blocked) |
| GET | `/admin/storage` | storage usage |
| POST | `/admin/garbage-collect` | run GC |
| GET | `/admin/mfa-policy` | read MFA policy |
| PATCH | `/admin/mfa-policy` | set optional|required |
| GET | `/admin/audit/verify-chain` | verify audit hash chain |
| GET | `/admin/roles`, `/admin/roles/{id}` | role management |
| POST | `/admin/roles`, `PATCH /admin/roles/{id}`, `DELETE /admin/roles/{id}` | role CRUD |

## Request/response notes

- Pagination: `page`, `page_size` (1–100).
- Uploads: `MAX_UPLOAD_SIZE_BYTES` enforced (413).
- Crypto paths (`/encryption/text/*`, `/files/upload|download`) share a
  per-IP crypto rate limit (`RATE_LIMIT_CRYPTO_PER_MINUTE`, default 20).
- Idempotency: `X-Idempotency-Key` (8–64 chars); replays return the
  original result.
- All list endpoints return `{items: [...], total, page, page_size}`.
