# SecureVault — Testing

## Backend

```bash
cd backend
.venv/bin/python -m pytest tests/ -q --tb=short
.venv/bin/python -m pytest tests/ -q --cov=app --cov-report=term   # coverage
.venv/bin/python -m pytest tests/test_integration_security.py      # one file
```

- ~240 tests / ~90% coverage across `app` (target 80%+).
- Tests run on an in-memory SQLite database with StaticPool; identity is
  seeded per test; the app's `get_db` dependency is overridden and
  rate-limiters are reset between tests. No PostgreSQL/Redis needed.

## Test areas

| Area | Files |
| --- | --- |
| Crypto primitives | `test_aes_gcm.py`, `test_aes_key_sizes.py`, `test_aes_tampering.py`, `test_rsa_service.py`, `test_hybrid_encryptor.py`, `test_sha256*.py`, `test_argon2*.py` |
| Streaming | `test_encrypt_stream.py`, `test_decrypt_stream.py`, `test_chunk_reader.py`, `test_chunk_writer.py`, `test_container_chunks.py` |
| Container & files | `test_container_serializer.py`, `test_file_encryptor.py`, `test_file_decryptor.py`, `test_folder_archiver.py`, `test_folder_encryptor.py` |
| Storage | `test_storage_engine.py`, `test_download_and_gc.py`, `test_retention.py` |
| Auth & tokens | `test_jwt_service.py`, `test_token_service.py`, `test_token_family.py`, `test_refresh_token_hashing.py`, `test_auth_service.py`, `test_session_key.py`, `test_session_id_generation.py`, `test_password_*.py`, `test_email_verification.py` |
| Enterprise features | `test_enterprise_features.py` (MFA, recovery codes, passkeys, sessions, roles, quotas, rate limits, pwned check) |
| API integration | `test_api_integration.py`, `test_integration_security.py` (auth lifecycle, token replay, MFA enforcement, RBAC mutation, IDOR, key expiry/rotation, AAD) |
| Middleware/observability | `test_middleware.py`, `test_rate_limiting.py`, `test_request_logging.py`, `test_health.py`, `test_key_material.py` |
| Key management | `test_key_management_service.py`, `test_wrap_unwrap_key.py` |
| Integrity/audit | `test_integrity_service.py`, `test_audit_chain.py` |

## What the security suite asserts

`test_integration_security.py`:
- expired access token → 401
- refresh rotation invalidates the old token; replay revokes the whole
  family (both old and rotated tokens die)
- logout revokes the refresh token
- refresh rejects access tokens (type confusion)
- MFA-enforced login issues no tokens; the MFA challenge cannot be used as
  an access token
- role removal revokes admin access immediately; Auditor cannot use admin
  endpoints
- cross-user file/folder/key access → 404 (IDOR matrix)
- expired keys are rejected for new encryption
- rotation revokes the old key, promotes the new one, and old containers
  remain decryptable
- AAD round-trip; missing/wrong AAD fails; oversized plaintext → 422

## Zip-bomb regression tests

`test_folder_archiver.py` builds a hand-crafted ZIP whose central directory
declares a 3 GiB member inside a ~130-byte file and asserts extraction is
rejected before writing, plus a cumulative-size-cap test.

## Frontend

The frontend is verified via the production build (`npm run build`,
includes `tsc -b`). No JS unit-test framework is currently configured.
