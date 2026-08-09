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
| `RATE_LIMIT_BACKEND` | multi-worker | `redis` with `REDIS_URL` |
| `ENABLE_SECURITY_HEADERS` | yes | on by default |
| `APP_ENV` | yes | `production` |

Do NOT commit `.env`; provision secrets via the platform's secret manager.

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
   `TRUSTED_PROXY_COUNT=1`.
2. Managed PostgreSQL with automated backups + point-in-time recovery.
3. `RATE_LIMIT_BACKEND=redis` if running more than one API worker.
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
- [ ] Redis rate limiting enabled for multi-worker
- [ ] Storage volume encrypted; backups verified
- [ ] Admin credentials rotated post-bootstrap
