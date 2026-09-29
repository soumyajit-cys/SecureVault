# SecureVault — Deployment

## Never commit secrets

Real credential values must never appear in tracked files — not in
`render.yaml` (`sync:` lines must always be bare `sync: false`,
"prompt in dashboard"), not in docs, not in tests. Guards:

- `.gitignore` excludes `.env`, `.env.*` (except `.env.example`), and
  `*.pem`. `.env` was never tracked; keep it that way.
- `.pre-commit-config.yaml` runs gitleaks on staged changes
  (`pip install pre-commit && pre-commit install` to activate).
- `.gitleaks.toml` pins the default ruleset plus a custom
  `render-sync-secret` rule that fails on any `sync: <value>` line,
  and CI (`.github/workflows/ci.yml`, `secrets-scan` job) scans every
  push/PR. Note the scanner's limit: stock gitleaks does not catch
  Render's split `key:`/`sync:` shape, which is why the custom rule
  exists — do not remove it.
- If a secret ever lands in git history, scrubbing the history does
  NOT un-leak it: rotate every exposed credential immediately (new
  Neon password, new Upstash DB/token, new `SECRET_KEY`, new admin
  password, new B2 application key), then rewrite history (see
  "Scrubbing git history" below) and force-push.

## Deploy order (Render + Vercel + Neon + Upstash + B2)

The frontend URL is needed by the backend (CORS, WebAuthn, emailed
links) and the backend URL is needed by the frontend, so deploy in
this order:

1. **Neon** — create the Postgres DB; copy the pooled connection URL.
   It must use the `postgresql+psycopg://` driver prefix (plain
   `postgresql://` is rejected at startup) and must NOT contain
   `channel_binding=require` (the pooler doesn't support it).
2. **Upstash** — create the Redis DB; copy the **Redis wire-protocol**
   URL (`rediss://default:<password>@<host>:6379`), NOT the REST URL
   (`https://...upstash.io`, rejected at startup).
3. **Backblaze B2** — create a bucket; note its region; create a
   bucket-scoped application key (never the master key).
4. **Render** — New → Blueprint with this repo's `render.yaml`; enter
   every `sync: false` value in the dashboard (Neon URL, Upstash URL,
   generated `SECRET_KEY`, admin password, B2 endpoint/bucket/key/secret,
   `WEBAUTHN_*`, `APP_BASE_URL` temporarily set to a placeholder).
   Deploy; note the backend URL (`https://<name>.onrender.com`).
5. **Vercel** — import `frontend/`; set `VITE_API_BASE` to
   `https://<render-backend>/api/v1`; deploy; note the frontend URL.
6. **Back to Render** — set the now-known URLs: `CORS_ALLOW_ORIGINS`
   to `["https://<vercel-app>"]`, `WEBAUTHN_RP_ID` to the backend host,
   `WEBAUTHN_ORIGIN` and `APP_BASE_URL` to the frontend origin.
   Redeploy and smoke-test (register → upload → download).

## Free-tier limitations

- **Cold starts**: the Render free web service sleeps after ~15 min
  idle; first request takes up to ~50 s. The frontend retries with
  backoff and shows a "Waking up the server" state (global banner +
  login/splash messaging) instead of a raw error.
- **No persistent disk**: `STORAGE_BACKEND=local` loses containers on
  every deploy/restart — use `STORAGE_BACKEND=s3` (B2) instead.
- **512 MB RAM**: the Docker image runs a single uvicorn worker
  (`--workers 1`); do not raise it without a bigger instance.
- **50 MB upload cap**: `MAX_UPLOAD_SIZE_BYTES=52428800` in
  `render.yaml` stays under free-tier request limits.
- **Neon free Postgres** is auto-deleted after 90 days of inactivity;
  back it up. **Render has no free managed Redis** — Upstash covers it.

## Environment variables

See `backend/.env.example` and `backend/app/core/config.py` for the full
list. Critical settings:

| Variable | Required | Notes |
| --- | --- | --- |
| `DATABASE_URL` | yes | `postgresql+psycopg://user:pass@host:5432/securevault` |
| `SECRET_KEY` | yes | at-rest master key; **must be unique, long, random**; rotate deliberately |
| `VAULT_ADMIN_EMAIL/USERNAME/PASSWORD` | yes | bootstrap admin |
| `CORS_ALLOW_ORIGINS` | prod | JSON list of exact origins, e.g. `["https://vault.example.com"]`; `*` with credentials is rejected at startup |
| `WEBAUTHN_RP_ID` / `WEBAUTHN_ORIGIN` / `APP_BASE_URL` | prod | backend host (no scheme), frontend origin, public frontend URL |
| `SECURE_COOKIES` / `COOKIE_SAMESITE` | prod | production forces `Secure` + `SameSite=None` for cross-origin auth |
| `TRUSTED_PROXY_COUNT` | prod | 1 when behind a TLS proxy |
| `RATE_LIMIT_BACKEND` | **mandatory in prod** | `redis` with `REDIS_URL`; startup refuses to run with the in-memory backend in production |
| `STORAGE_BACKEND` | when no persistent disk | `local` (default, disk under `STORAGE_DIR`) or `s3` (S3-compatible bucket) |
| `S3_ENDPOINT_URL/S3_BUCKET/S3_ACCESS_KEY/S3_SECRET_KEY` | with `STORAGE_BACKEND=s3` | missing values fail fast at startup, not on first upload |
| `S3_REGION` | with `STORAGE_BACKEND=s3` | e.g. `us-west-004` for Backblaze B2; default `us-west-004` |
| `ENABLE_SECURITY_HEADERS` | yes | on by default |
| `APP_ENV` | yes | `production` |

Do NOT commit `.env`; provision secrets via the platform's secret manager.
Startup validates formats before serving: `DATABASE_URL` needs the
`postgresql+psycopg://` prefix (no `channel_binding=require`);
`REDIS_URL` must be `redis(s)://` (Postgres and Upstash REST URLs are
rejected with a hint); `CORS_ALLOW_ORIGINS` must parse as a JSON list;
production enforces `SECRET_KEY` length/placeholder and admin-password
rules. See `backend/tests/test_config_validation.py` for the matrix.

## Scrubbing git history

If secrets were ever committed (e.g. values after `sync:` in an old
`render.yaml` revision), use **git filter-repo** (actively maintained;
BFG is effectively unmaintained and cannot do content replacement as
flexibly):

```bash
pip install git-filter-repo
# 1. Fresh mirror clone (never scrub in your working repo)
git clone --mirror <repo-url> securevault-scrub && cd securevault-scrub
# 2. Replace each leaked value. The file holds ONE rule per line in
#    `regex:PATTERN==>replacement` form (Python re syntax, so \1 is
#    the group reference). This rule redacts every `sync: <value>`
#    line but leaves `sync: false` and CHANGEME placeholders alone.
printf '%s\n' 'regex:(?m)^(\s*sync:\s*)(?!false\b)(?!CHANGEME)\S+==>\1[REDACTED]' > sync.txt
git filter-repo --replace-text sync.txt --force
# 3. Inspect: git log -p -- render.yaml must show no real values, then
git push --force --all && git push --force --tags
```

Then: **rotate everything first** (scrubbing hides history but anyone
who cloned already has the secrets), tell collaborators to re-clone
(fetched deltas won't reconcile), and confirm the gitleaks CI job is
green before merging anything else.

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
