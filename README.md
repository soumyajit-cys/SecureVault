# SecureVault

Enterprise-grade server-side encryption and secure file management platform.

SecureVault protects sensitive data with **AES-256-GCM** authenticated
encryption: files are sealed with per-message session keys, each session key
is wrapped with a per-user **RSA-4096** parent key, passwords are hashed with
**Argon2id**, and every security-relevant action is logged to an audit trail
with hash-chain integrity and RBAC-aware access control.

## Security model (read this first)

SecureVault is **server-side encrypted with server-held key custody**. It is
**not a zero-knowledge / end-to-end-encrypted service**:

- The server generates the per-user RSA parent keys.
- The server stores the RSA private keys in the database, encrypted at rest
  with a master key derived from `SECRET_KEY`.
- The server necessarily holds plaintext in memory while encrypting or
  decrypting, and an operator who controls the server (or its database and
  secret material) can decrypt stored files.

Data *at rest* on the storage volume is ciphertext; the plaintext never
touches the disk in the normal flow, and a storage-volume compromise alone
does not expose file contents. See [docs/security.md](docs/security.md) for
the detailed security model, key-custody analysis and the architectural
changes required for true zero-knowledge.

## Features

- **Cryptography**
  - AES-256-GCM authenticated encryption with optional AAD
  - per-message session keys wrapped with RSA-4096 OAEP
  - SHA-256 integrity verification on every container
  - Streaming encryption/decryption for files of arbitrary size
  - SecureVault binary container format (magic + versioned header)

- **Key management**
  - Server-side key generation, rotation and revocation
  - Key expiry (expired keys are rejected for new encryptions),
    fingerprinting and replacement tracking

- **Storage engine**
  - Layout-isolated encrypted containers (one file = one container)
  - Streaming upload (encrypt) and download (decrypt + verify)
  - Folder archive encryption (zip + AES-GCM) and safe restore
  - Zip-bomb protection (size caps, compression-ratio guard)
  - Soft-delete, garbage collection and temp-file cleanup
  - Idempotent uploads and multi-field file search (pg_trgm)

- **Security & auth**
  - Argon2id password hashing, account lockout, deactivation
  - RSA-256-signed JWTs with rotated signing keys (at-rest wrapped)
  - Rotating refresh tokens (family detection, replay protection)
  - TOTP MFA with recovery codes and enforced-MFA policy
  - WebAuthn passkey registration and login (FIDO2)
  - Role-based access control (`User`, `Admin`, `Auditor`)
  - Hash-chained audit trail (`user.*`, `file.*`, `folder.*`, `key.*`,
    `admin.*`, `device.*`) with CSV export

- **Operations & hardening**
  - Liveness/readiness probes (`/health/live`, `/health/ready`)
  - Prometheus-format metrics (`/metrics`)
  - Per-IP rate limiting (login + crypto paths) with trusted-proxy-aware
    `X-Forwarded-For` handling
  - Security headers, CORS, request IDs, structured JSON logs
  - Global exception handling that never leaks stack traces or secrets
  - Path-traversal-safe storage, ownership-scoped queries (no IDOR)

## Stack

| Layer    | Technology                                    |
| -------- | --------------------------------------------- |
| Backend  | Python 3.13, FastAPI, SQLAlchemy 2, Alembic   |
| Storage  | PostgreSQL (prod) / SQLite (tests)            |
| Crypto   | `cryptography`, `argon2-cffi`                 |
| Frontend | React 18, TypeScript, Vite 5, Tailwind 3      |

## Getting started

### Backend

```bash
cp .env.example .env               # configure DATABASE_URL, SECRET_KEY, etc.
python -m venv .venv && source .venv/bin/activate
pip install -r backend/requirements.txt
cd backend
alembic upgrade head
uvicorn app.main:app --reload     # startup seeds roles/permissions + links
                                  # and creates the admin account (VAULT_ADMIN_*)
```

Health check: http://localhost:8000/api/v1/health
Interactive API docs: http://localhost:8000/docs

### Frontend

```bash
cd frontend
npm install
npm run dev        # dev server on :5173, proxies /api → :8000
npm run build      # static production bundle in dist/
```

### Tests

```bash
cd backend
.venv/bin/python -m pytest tests/ -q --cov=app --cov-report=term
```

238+ tests (including parameterized crypto tamper cases), ~90% coverage
across `app` modules.

## API overview

Base path: `/api/v1`. All endpoints except auth/health require
`Authorization: Bearer <access_token>`.

- **Health** — `GET /health` · `/health/live` · `/health/ready` · `/metrics`
- **Auth** — `POST /auth/register` · `/login` · `/refresh` · `/logout` ·
  `/change-password` · `POST /auth/verify-email` · `/password-reset/request` ·
  `/password-reset/confirm` · MFA: `GET /auth/mfa/status` ·
  `POST /auth/mfa/setup|enable|disable|verify` · Passkeys:
  `POST /auth/passkeys/register/{begin|complete}` · `/passkeys/login/...` ·
  `GET|DELETE /auth/passkeys` · Sessions: `GET /auth/sessions` ·
  `DELETE /auth/sessions/{id}` · `POST /auth/sessions/revoke-all`
- **Profile** — `GET /profile/me`
- **Encryption** — `POST /encryption/text/encrypt|decrypt` (optional AAD)
- **Files** — `POST /files/upload` (idempotency key) · `GET /files` (search,
  filters) · `/files/summary` · `GET /files/{id}` · `GET /files/{id}/download`
  · `PATCH /files/{id}` · `DELETE /files/{id}`
- **Folders** — `POST /folders/upload` · `GET /folders` ·
  `POST /folders/{id}/restore`
- **Keys** — `POST /keys` · `GET /keys` · `GET /keys/active` · `GET /keys/{id}`
  · `POST /keys/rotate` · `POST /keys/{id}/revoke`
- **Audit** — `GET /audit/logs` · `GET /audit/admin/logs` (admin) · CSV export
- **Admin** — `GET /admin/users` · activate/deactivate · `GET /admin/storage` ·
  `POST /admin/garbage-collect` · `GET|PATCH /admin/mfa-policy` ·
  `GET /admin/audit/verify-chain`

## Architecture

```
backend/app/
├── api/
│   ├── dependencies/        # DB, auth, RBAC, storage DI
│   └── routes/              # auth, profile, encryption, files, folders,
│                            # keys, audit, admin, health, metrics
├── core/                    # config, middleware (CORS, rate limit, tracing),
│                            # logging, metrics registry, at-rest crypto
├── crypto/                  # AES-GCM, RSA/hybrid, hashing, streaming, header
├── domain/                  # models, repository ports, constants
├── infrastructure/          # SQLAlchemy repositories, storage layout
├── schemas/                 # pydantic request/response models
├── services/                # auth, encryption, storage, key mgmt, audit
├── scripts/                 # identity seeding, maintenance
└── main.py                  # FastAPI app, routers, lifespan, exception handler

frontend/
└── src/
    ├── components/          # layout, guards, ui kit
    ├── lib/                 # axios client (JWT refresh), endpoints, format
    ├── pages/               # dashboard, crypto, files, folders, keys,
    │                        # audit, profile, settings, admin, landing
    ├── store/               # zustand auth store
    └── types/               # shared API types
```

### Crypto design

1. Every vault user owns parent RSA-4096 keys (`CryptoKey` rows). The server
   generates them and stores the private halves at-rest encrypted.
2. To store a file, the server generates a fresh AES-256 session key, encrypts
   the payload, wraps the session key with the RSA public key and stores only
   the container (magic + header + nonce + ciphertext + tag + wrapped key).
3. On download, the container header is validated, the session key unwrapped
   with the RSA private key, integrity verified and the file streamed-decrypted.
4. Folder uploads ZIP the tree recursively (streaming), then encrypt the
   archive; restore reverses the process with traversal and zip-bomb guards.
5. Key rotation issues a new parent key; new files use it. Revocation blocks
   usage; old containers remain readable by their recorded key.

### Data model

`User` → `Role` / `UserRole` / `Permission`; `RefreshToken` (families + replay
protection); `CryptoKey` (lifecycle, fingerprints); `StoredFile` (metadata,
sizes, sha256, folders, soft-delete, idempotency keys); `AuditLog` (hash
chain); `Session` (device fingerprints); `WebAuthnCredential`; `AppSetting`
(MFA policy).

Migrations live in `backend/alembic/versions/`.

## Configuration (`.env`)

Start from `.env.example`. Key settings (see `backend/app/core/config.py`):

| Variable | Default | Purpose |
| -------- | ------- | ------- |
| `DATABASE_URL` | — | SQLAlchemy DSN (PostgreSQL) |
| `SECRET_KEY` | — | master key for at-rest wrapping (signing keys, user private keys) |
| `JWT_ALGORITHM` | `RS256` | token signing algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `15` | access token lifetime |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `7` | refresh token lifetime |
| `MAX_LOGIN_ATTEMPTS` | `5` | lockout threshold |
| `ACCOUNT_LOCK_MINUTES` | `15` | lockout duration |
| `VAULT_ADMIN_EMAIL` | — | bootstrap admin email (created on first startup) |
| `VAULT_ADMIN_USERNAME` | — | bootstrap admin username (default `admin`) |
| `VAULT_ADMIN_PASSWORD` | — | bootstrap admin password |
| `MAX_UPLOAD_SIZE_BYTES` | 4 GiB | max upload size |
| `STORAGE_DIR` | `storage/` | vault container layout |
| `GARBAGE_COLLECTION_ENABLED` | `true` | cleanup task toggle |
| `RATE_LIMIT_BACKEND` | `local` | `local` or `redis` rate limiting |

## Deployment (production)

- Run migrations with `alembic upgrade head`; roles/permissions are seeded
  automatically by the app startup hook.
- Serve the API with `uvicorn app.main:app` behind a TLS reverse proxy
  (nginx / Caddy) with `TRUSTED_PROXY_COUNT` configured.
- Serve the built React app (`frontend/dist`) behind the same origin and
  forward `/api` to the API server.
- Use a managed PostgreSQL instance, a strong unique `SECRET_KEY` (rotating it
  re-wraps at-rest material on next access), and enable Redis-backed rate
  limiting for multi-worker deployments.
- See [docs/deployment.md](docs/deployment.md) for the full checklist and the
  Docker Compose stack.

## Documentation

See `docs/` for the complete v1.0 documentation:

- [architecture.md](docs/architecture.md) — system structure and data flow
- [security.md](docs/security.md) — security model, key custody, hardening
- [cryptography.md](docs/cryptography.md) — algorithms, container format
- [authentication.md](docs/authentication.md) — auth flows, MFA, WebAuthn
- [authorization.md](docs/authorization.md) — RBAC model and permissions
- [storage.md](docs/storage.md) — storage engine and file lifecycle
- [database.md](docs/database.md) — schema, indexes, migrations
- [api.md](docs/api.md) — endpoint reference
- [deployment.md](docs/deployment.md) — production deployment
- [testing.md](docs/testing.md) — running the test suites
- [threat-model.md](docs/threat-model.md) — threat model and mitigations
