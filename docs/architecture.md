# SecureVault — Architecture

## System overview

SecureVault is a three-tier application:

1. **React SPA** (`frontend/`) — Vite + TypeScript + Tailwind. Serves the UI
   and calls the API exclusively through a JSON API with bearer-token auth.
2. **FastAPI backend** (`backend/app`) — REST API, authentication,
   authorization, crypto services, storage engine, audit trail.
3. **PostgreSQL** — system of record: users, roles, keys, file metadata,
   sessions, audit logs. **Redis** (optional) — rate-limit state for
   multi-worker deployments.

The frontend never receives or stores cryptographic key material. All
encryption/decryption happens server-side (see `docs/security.md` for the
key-custody model).

## Backend layering

```
routes (HTTP, validation, authz deps)
   │
dependencies (DI: get_db, get_current_user, services)
   │
services (business logic: auth, crypto, storage, key mgmt, audit)
   │
domain (ports: repository ABCs, models, constants)
   │
infrastructure (adapters: SQLAlchemy repositories, disk layout)
   │
crypto (pure primitives: AES-GCM, RSA, hybrid, hashing, streams)
```

- **Routes** are thin: parse/validate with Pydantic schemas, enforce
  authentication via `get_current_user`, enforce authorization via
  `require_permission`, delegate to a service, map exceptions to HTTP.
- **Services** hold the business rules (key lifecycle, rotation, quota,
  lockout, MFA verification, audit chaining).
- **Domain interfaces** define repository contracts; **infrastructure**
  implements them with SQLAlchemy. Tests swap the database via a dependency
  override (`app.api.dependencies.database.get_db`).
- **Crypto** is a leaf package with no HTTP or persistence dependencies.

## Request lifecycle

1. Middleware order: CORS → security headers → request ID → logging →
   rate limiting → routing.
2. `RequestIDMiddleware` assigns `X-Request-ID`; structured logs carry
   `request_id`, and `bind_actor` adds `user_id`/`session_id` once the token
   is decoded.
3. Authentication: `HTTPBearer` extracts the token; `get_current_user`
   verifies signature against the rotating `jwt_signing_keys` table,
   validates `token_type == "access"`, resolves the user, and binds actor
   context for audit logging.
4. Authorization: `require_permission` checks the user's role permissions
   (Admin = `*`).
5. Business logic runs in a service; audit events are written to the
   hash-chained `audit_logs` table; exceptions map to clean JSON errors
   via the global `SecureVaultException` handler.

## Key modules

| Module | Responsibility |
| --- | --- |
| `app/main.py` | App factory, middleware, routers, lifespan (seed + GC) |
| `app/core/config.py` | Settings (env-driven, pydantic) |
| `app/core/at_rest.py` | Master-key derivation and at-rest wrapping |
| `app/core/key_material.py` | Purpose-scoped key derivation (at-rest vs wrap) |
| `app/core/middleware.py` | Security headers, rate limit, request IDs |
| `app/crypto/aes/aes_gcm.py` | AES-GCM primitive (AAD-capable) |
| `app/crypto/rsa/hybrid_encryptor.py` | Hybrid AES+RSA encryption |
| `app/crypto/streams/` | Streaming encrypt/decrypt (4 MiB chunks) |
| `app/services/encryption/` | File/folder encryptors, container serializer |
| `app/services/storage/` | Upload, download, metadata, GC, quota |
| `app/services/auth/` | Auth flows, JWT, refresh rotation, MFA, WebAuthn |
| `app/services/key_management_service.py` | Key lifecycle + private-key unlock |
| `app/services/audit_service.py` | Hash-chained audit writes |

## Frontend structure

- `src/lib/api.ts` — axios instance with bearer-token request interceptor and
  silent refresh-on-401 response interceptor.
- `src/lib/endpoints.ts` — typed endpoint wrappers (no trailing slashes, which
  avoids 307 redirects that strip auth headers).
- `src/store/` — zustand auth store (tokens in localStorage, `auth:logout`
  events on refresh failure).
- `src/pages/` — feature pages; `src/components/guards/` — route guards for
  authentication and admin-only areas.

## Data flow for a file upload

```
browser ── multipart ──► POST /api/v1/files/upload
   └─► UploadService (streams to temp path, enforces size limit)
        └─► FileEncryptor (AES session key, RSA wrap, container format)
             └─► StorageService (atomic move into vault layout)
                  └─► MetadataService (StoredFile row) ──► audit event
```

Download reverses the pipeline with SHA-256 verification before the file
leaves the server.
