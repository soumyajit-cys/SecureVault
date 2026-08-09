# SecureVault — Database

## Engine

- **PostgreSQL** in production (SQLAlchemy 2.0, `psycopg` driver), SQLite
  in tests (inline StaticPool, seeded identity).
- DSN from `DATABASE_URL`.
- Migrations via Alembic (`backend/alembic/versions/`); the deployed
  database must be at head (currently `5c0705199c28`).

## Models

| Model | Purpose | Key fields |
| --- | --- | --- |
| `User` | Account | email (unique), username, password hash, totp_secret, recovery codes hash, lockout counters, deactivated, verified_at |
| `Role` / `UserRole` / `RolePermission` / `Permission` | RBAC | name, permission strings |
| `RefreshToken` | Refresh rotation | token_hash (unique), token_family, session_id, revoked, replaced_by_token, expires_at |
| `Session` | Device sessions | session_identifier (unique), device_fingerprint, device_name, ip, user_agent, revoked, expires_at |
| `CryptoKey` | Vault keys | user_id, name, algorithm, key_size, status (active/revoked/expired), fingerprint, public_key_pem, encrypted_private_key_pem, nonce/tag/salt, expires_at, replaced_by_key_id |
| `JwtSigningKey` | Token signing | algorithm, status, wrapped private key material, rotated_at |
| `StoredFile` | Vault items | user_id, original_filename, mime_type, original_size, encrypted_size, sha256, is_folder, status, deleted_at, key_id, idempotency_key, folder metadata |
| `AuditLog` | Audit trail | user_id, action, details, ip, user_agent, prev_hash, hash (chain) |
| `EmailVerificationToken` / `PasswordResetToken` | Flows | hashed token, expiry, consumed |
| `MfaRecoveryCode` | Recovery | hashed code, used |
| `WebAuthnCredential` | Passkeys | user_id, credential_id, public key, sign_count, transports, name |
| `AppSetting` | Global config | key/value (`mfa_policy`, …) |

All primary keys are UUIDs; timestamp columns use UTC.

## Notable indexes & constraints

- `users.email` unique; `refresh_tokens.token_hash` unique;
  `sessions.session_identifier` unique.
- `stored_files`: index on `user_id`, `(user_id, status)`, and a
  **pg_trgm GIN index** (`gin_trgm_ops`) on `original_filename` for
  fuzzy-substring search; `idempotency_key` unique per user.
- `audit_logs`: index on `(user_id, created_at)`.
- Foreign keys with ON DELETE CASCADE for dependent rows
  (refresh tokens, sessions, user roles).

## Audit hash chain

Each `AuditLog` row stores `prev_hash` (SHA-256 of the previous row's
canonical serialization) and its own hash. The chain is verified by
`/admin/audit/verify-chain` and `IntegrityService`; a tampered history row
breaks the chain. `DATA_RETENTION_DAYS` / `ENABLE_RIGHT_TO_ERASURE` control
retention purges.

## Migrations

```bash
cd backend
alembic upgrade head     # apply
alembic downgrade -1     # roll back one revision
```

Migrations are revision-linear (single head). Startup seeding creates
permissions, roles, and role-permission links idempotently, and bootstraps
the admin user from `VAULT_ADMIN_*` when missing.

## Test database behavior

The test fixture creates a fresh in-memory SQLite schema per test
(`Base.metadata.create_all`), seeds identity, overrides `get_db`, and
resets rate-limiters between tests — no PostgreSQL dependency for unit or
API tests.
