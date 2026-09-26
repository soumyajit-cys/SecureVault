# SecureVault — Deployment

## Environment variables

See `backend/.env.example` and `backend/app/core/config.py` for the full
list. Critical settings:

| Variable | Required | Notes |
| --- | --- | --- |
| `DATABASE_URL` | yes | `postgresql+psycopg://user:pass@host:5432/securevault` |
| `SECRET_KEY` | yes | at-rest master key; **must be unique, long, random**; rotate deliberately |
| `VAULT_ADMIN_EMAIL/USERNAME/PASSWORD` | yes | bootstrap admin |
| `CORS_ALLOW_ORIGINS` | prod | restrict to your origin, e.g. `["https://vault.example.com"]` |
| `TRUSTED_PROXY_COUNT` | prod | 1 when behind a TLS proxy |
| `RATE_LIMIT_BACKEND` | **mandatory in prod** | `redis` with `REDIS_URL`; startup refuses to run with the in-memory backend in production |
| `STORAGE_BACKEND` | when no persistent disk | `local` (default, disk under `STORAGE_DIR`) or `s3` (S3-compatible bucket) |
| `S3_ENDPOINT_URL/S3_BUCKET/S3_ACCESS_KEY/S3_SECRET_KEY` | with `STORAGE_BACKEND=s3` | missing values fail fast at startup, not on first upload |
| `S3_REGION` | with `STORAGE_BACKEND=s3` | e.g. `us-west-004` for Backblaze B2; default `us-west-004` |
| `ENABLE_SECURITY_HEADERS` | yes | on by default |
| `APP_ENV` | yes | `production` |

Do NOT commit `.env`; provision secrets via the platform's secret manager.

## Object storage (S3-compatible)

Render's free tier has no persistent disk, so `STORAGE_BACKEND=local`
loses every committed container on each deploy/restart. Point
SecureVault at an S3-compatible bucket instead — Backblaze B2 is the
reference target, but any S3 API (AWS S3, MinIO, …) works because the
client is configured with `endpoint_url`.

```bash
STORAGE_BACKEND=s3
S3_ENDPOINT_URL=https://s3.us-west-004.backblazeb2.com
S3_BUCKET=securevault-containers
S3_ACCESS_KEY=<b2-application-key-id>
S3_SECRET_KEY=<b2-application-key-secret>
S3_REGION=us-west-004
```

Backblaze B2 specifics:

- **Endpoint format** is `https://s3.<region>.backblazeb2.com` — find the
  region on your bucket's info page (B2 names them like `us-west-004`,
  `eu-central-003`). `S3_REGION` must match; it signs requests (SigV4).
- **Keys**: create an *application key* scoped to the bucket with
  read/write (not the master key). The key ID is `S3_ACCESS_KEY`, the key
  itself is `S3_SECRET_KEY`.
- **Behavior**: committed `.svlt` containers stream into the bucket via
  multipart upload (8 MiB parts, bounded RAM); downloads stream back
  through ranged/sequential reads. Staged uploads and folder-restores
  still use ephemeral local disk — transient per-request scratch that
  needs no persistence. Container keys (`files/<user>/<file>.svlt`) are
  identical in both backends, so existing `storage_path` rows stay valid
  if you migrate objects with the same keys.
- Startup validates the `S3_*` fields before serving traffic; the
  backend suite covers the S3 path with `moto`
  (`backend/tests/test_s3_storage.py`, no real credentials needed).

## Docker Compose

`docker-compose.yml` (root) provides:

- `db` — PostgreSQL 16 with healthcheck.
- `api` — the backend image (`Dockerfile` at root), `SECRET_KEY` required
  via `${SECRET_KEY:?}`, volume-mounted vault storage.

```bash
SECRET_KEY="$(openssl rand -hex 32)" docker compose up --build
```

The Compose stack is a development/self-hosting baseline. For production:

1. **TLS termination** at a reverse proxy (nginx/Caddy) with
   `TRUSTED_PROXY_COUNT=1`. TLS is required anyway for Secure cookie
   attributes (refresh token + CSRF cookies are `Secure` in production).
2. Managed PostgreSQL with automated backups + point-in-time recovery.
3. **Redis** for the rate limiter (`RATE_LIMIT_BACKEND=redis`,
   `REDIS_URL=...`) — enforced at startup in production.
4. Volume encryption for `vault-storage` (LUKS at the host, or
   provider-managed encryption).
5. Run the frontend as a static bundle (`frontend/dist`) served by the
   proxy, proxying `/api` to the API container.

## Backend run modes

```bash
cd backend
alembic upgrade head
uvicorn app.main:app --workers 4        # multi-worker (Redis rate limit)
gunicorn app.main:app -k uvicorn.workers.UvicornWorker -w 4
```

Startup performs idempotent seeding (permissions, roles, role-links, admin)
and optionally starts the background GC task.

## Health & readiness

- `/health/live` — process alive.
- `/health/ready` — verifies DB connectivity (fails during migration/DB
  outage; wire into orchestrator readiness probes).
- `/metrics` — Prometheus scrape target (`vault_requests_total`,
  `vault_request_duration_seconds`, uptime).

## Release checklist

- [ ] `alembic upgrade head` on a clean database, then seed + smoke test
- [ ] Backend suite green (`pytest tests/ -q --cov=app`)
- [ ] Frontend `npm run build` succeeds; serve `dist/`
- [ ] `SECRET_KEY` provisioned (never default)
- [ ] CORS restricted; `TRUSTED_PROXY_COUNT` set; TLS enabled
- [ ] Redis rate limiting enabled and reachable (required in production)
- [ ] Storage volume encrypted; backups verified (or `STORAGE_BACKEND=s3`
  with a versioned bucket + lifecycle rules when there is no persistent disk)
- [ ] Admin credentials rotated post-bootstrap
