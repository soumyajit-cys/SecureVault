# SecureVault

Enterprise-grade encryption and secure file management platform.

SecureVault protects sensitive data end-to-end: files are sealed with
**AES-256-GCM**, per-message keys are wrapped with the user's RSA key, passwords
are hashed with **Argon2id**, and every security-relevant action is logged to an
immutable audit trail with RBAC-aware access control.

## Features

- **Cryptography**
  - AES-256 / AES-128 GCM authenticated encryption with AAD
  - ChaCha20 flavor (negotiable per-key by vault policy)
  - per-message sealed keys wrapped with RSA-4096 / RSA-2048
  - SHA-256 integrity verification on every container
  - Streaming encryption for files of arbitrary size

- **Key management**
  - Server-side key generation, rotation and revocation
  - Key expiry, fingerprinting and replacement tracking

- **Storage engine**
  - Layout-isolated encrypted containers (one file = one container)
  - Upload (streaming encrypt), download (streaming decrypt + verify)
  - Folder archive encryption (zip + AES-GCM) and safe restore
  - Soft-delete, garbage collection and temp-file cleanup
  - Optional background cleanup task

- **Security & auth**
  - Argon2id password hashing
  - JWT access + rotating refresh tokens (family detection, replay protection)
  - Account lockout after failed attempts, deactivation
  - Role-based access control (`User`, `Admin`, `Auditor`)
  - Full audit trail (`user.*`, `file.*`, `folder.*`, `key.*`, `admin.*`)
  - Global exception handling, request validation, max upload enforcement

- **API**
  - `Auth` — register, login, refresh, logout, change password
  - `Encryption` — text encrypt / decrypt
  - `Files` — upload, list, metadata, download, rename, soft-delete, summary
  - `Folders` — archive upload, list, restore
  - `Keys` — generate, list, rotate, revoke
  - `Audit` — log stream (exports too)
  - `Admin` — storage usage, garbage collection, user management

- **Frontend (React + TypeScript + Vite + Tailwind)**
  - Dark "cyber vault" UI; login/register, dashboard, text & file crypto,
    folder tools, key manager, audit logs, settings and an admin panel

## Stack

| Layer    | Technology                                    |
| -------- | --------------------------------------------- |
| Backend  | Python 3.13, FastAPI, SQLAlchemy 2, Alembic   |
| Storage  | PostgreSQL (prod) / SQLite (tests)            |
| Crypto   | `cryptography`, `pycryptodome`, `argon2-cffi` |
| Frontend | React 18, TypeScript, Vite 5, Tailwind 3      |

## Getting started

### Backend

```bash
cp .env.example .env               # configure DATABASE_URL, JWT secret, etc.
python -m venv .venv && source .venv/bin/activate
pip install -r backend/requirements.txt
cd backend
alembic upgrade head
uvicorn app.main:app --reload     # startup seeds roles/permissions (Admin, User, Auditor)
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
source ../.venv/bin/activate
python -m pytest tests/ -q --cov=app --cov-report=term
```

141 tests — 88% coverage across app modules.

## API overview

Base path: `/api/v1`

- `POST /auth/register` · `POST /auth/login` · `POST /auth/refresh` · `POST /auth/logout` · `POST /auth/change-password`
- `GET  /profile/me`
- `POST /encryption/text/encrypt` · `POST /encryption/text/decrypt`
- `POST /files/upload` · `GET /files` · `GET /files/summary` · `GET /files/{id}` · `GET /files/{id}/download` · `PATCH /files/{id}` · `DELETE /files/{id}`
- `POST /folders/upload` · `GET /folders` · `POST /folders/{id}/restore`
- `POST /keys` (generate) · `GET /keys` · `GET /keys/active` · `GET /keys/{id}` · `POST /keys/rotate` · `POST /keys/{id}/revoke`
- `GET /audit/logs` · `GET /audit/admin/logs`
- `GET /admin/status` · `GET /admin/users` · `POST /admin/users/{id}/activate|deactivate` · `GET /admin/storage` · `POST /admin/garbage-collect`

All endpoints except auth/health require `Authorization: Bearer <access_token>`.

## Architecture

```
backend/app/
├── api/
│   ├── dependencies/        # DB, auth, RBAC, storage DI
│   └── routes/              # auth, profile, encryption, files, folders,
│                            # keys, audit, admin, health
├── crypto/                  # low-level crypto services (AES-GCM, RSA, hashing)
├── domain/                  # models, repositories (ports), constants
├── infrastructure/          # SQLAlchemy repositories, storage layout
├── schemas/                 # pydantic request/response models
├── services/                # encryption, storage, key mgmt, audit, auth
├── scripts/                 # identity seeding, maintenance
└── main.py                  # FastAPI app, routers, lifespan, exception handler

frontend/
└── src/
    ├── components/          # layout, guards, ui kit
    ├── lib/                 # axios client (JWT refresh), endpoints, format
    ├── pages/               # dashboard, crypto, files, folders, keys,
    │                        # audit, profile, settings, admin
    ├── store/               # zustand auth store
    └── types/               # shared API types
```

### Crypto design

1. Every vault user owns parent RSA keys (`CryptoKey` rows).
2. To store a file, the server generates a fresh AES message key, encrypts the
   payload, encrypts (wraps) the message key with the RSA public key and
   stores only the container (header + nonce + ciphertext + tag + signature).
3. On download, integrity is verified and the file is streamed-decrypted.
4. Folder uploads ZIP the tree recursively, then encrypt the archive.
5. Key rotation issues a new parent key; new files use it. Revocation blocks
   usage; old containers remain readable by their recorded key.

### Data model

`User` → `Role` / `UserRole` / `Permission`; `RefreshToken` (families + replay
protection); `CryptoKey` (lifecycle, fingerprints); `StoredFile` (metadata,
sizes, sha256, folders, soft-delete); `AuditLog`; `Session`.

Migrations live in `backend/alembic/versions/`.

## Configuration (`.env`)

Start from `.env.example`. Key settings (see `backend/app/core/config.py`):

| Variable | Default | Purpose |
| -------- | ------- | ------- |
| `DATABASE_URL` | — | SQLAlchemy DSN (PostgreSQL) |
| `SECRET_KEY` | — | JWT signing secret (rotate per deploy) |
| `JWT_ALGORITHM` | `HS256` | token signing algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `15` | access token lifetime |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `7` | refresh token lifetime |
| `MAX_LOGIN_ATTEMPTS` | `5` | lockout threshold |
| `ACCOUNT_LOCK_MINUTES` | `15` | lockout duration |
| `MAX_UPLOAD_SIZE_BYTES` | 4 GiB | max upload size |
| `STORAGE_DIR` | `storage/` | vault container layout |
| `GARBAGE_COLLECTION_ENABLED` | `true` | cleanup task toggle |

## Deployment (production)

- Run migrations with `alembic upgrade head`; roles/permissions are seeded
  automatically by the app startup hook.
- Serve the API with `uvicorn app.main:app` behind a TLS proxy (nginx / Caddy).
- Serve the built React app (`frontend/dist`) behind the same origin
  reverse proxy and forward `/api` to the API server.
- Configure `DATABASE_URL` to a managed PostgreSQL instance, rotate `SECRET_KEY`
  at deploy, and enable the background garbage-collection task via lifespan
  (default on).
- Data-at-rest encryption for the vault directory (see `StorageService`) is
  enforced: plaintext is never written to the vault layout.