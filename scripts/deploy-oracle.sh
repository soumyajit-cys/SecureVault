#!/usr/bin/env bash
#
# deploy-oracle.sh — one-command production deploy for SecureVault
# on Oracle Cloud "Always Free" (or any single VM with Docker).
#
# Automates:
#   1. Secret generation (idempotent — never overwrites existing .env)
#   2. docker compose build + up (Postgres + Redis + API)
#   3. HTTPS via Caddy with a domain, or Cloudflare Tunnel without one
#   4. Nightly Postgres backup + keep-alive crons
#
# Usage (run on the VM, inside the repo root):
#
#   ./scripts/deploy-oracle.sh
#   DOMAIN=vault.example.com ./scripts/deploy-oracle.sh      # Caddy mode
#   CF_TUNNEL_TOKEN=... ./scripts/deploy-oracle.sh           # Cloudflare Tunnel mode
#
# Optional overrides (export before running):
#   VAULT_ADMIN_EMAIL / VAULT_ADMIN_USERNAME  (bootstrap admin identity)
#   CORS_ORIGINS  e.g. '["https://vault.example.com","https://vault.pages.dev"]'
#   STORAGE_KEEP_DAYS=30  (backup retention)

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="$ROOT/.env"
COMPOSE="docker compose"

c_green='\033[0;32m'; c_red='\033[0;31m'; c_yellow='\033[1;33m'; c_bold='\033[1m'; c_reset='\033[0m'
info()  { printf "${c_green}[*]${c_reset} %s\n" "$*"; }
warn()  { printf "${c_yellow}[!]${c_reset} %s\n" "$*"; }
die()   { printf "${c_red}[x]${c_reset} %s\n" "$*" >&2; exit 1; }

cd "$ROOT"

command -v docker >/dev/null || die "docker is not installed. Run: curl -fsSL https://get.docker.com | sh"
$COMPOSE version >/dev/null 2>&1 || COMPOSE=docker-compose
command -v curl >/dev/null || die "curl is required"

# ---------- 1. Secrets & env (idempotent) ----------

touch "$ENV_FILE"
chmod 600 "$ENV_FILE"

env_get() { grep -E "^$1=" "$ENV_FILE" | head -1 | cut -d= -f2- || true; }
env_set() { # name value — keeps existing values, appends missing ones
  if ! grep -qE "^$1=" "$ENV_FILE"; then
    printf '%s=%s\n' "$1" "$2" >> "$ENV_FILE"
    info "generated $1"
  fi
}

rand_hex() { openssl rand -hex "${1:-32}"; }
rand_b64() { openssl rand -base64 18 | tr -d '\n'; }

SECRET_KEY="$(env_get SECRET_KEY)";           [ -n "$SECRET_KEY" ]           || env_set SECRET_KEY "$(rand_hex 32)"
POSTGRES_PASSWORD="$(env_get POSTGRES_PASSWORD)"; [ -n "$POSTGRES_PASSWORD" ] || env_set POSTGRES_PASSWORD "$(rand_hex 24)"

VAULT_ADMIN_PASSWORD="$(env_get VAULT_ADMIN_PASSWORD)"
if [ -z "$VAULT_ADMIN_PASSWORD" ]; then
  env_set VAULT_ADMIN_PASSWORD "$(rand_b64)"
  warn "VAULT_ADMIN_PASSWORD generated — save it from the summary below!"
fi

ADMIN_EMAIL="$(env_get VAULT_ADMIN_EMAIL)"
ADMIN_EMAIL="${ADMIN_EMAIL:-admin@example.com}"
if [ -z "$(env_get VAULT_ADMIN_EMAIL)" ]; then
  env_set VAULT_ADMIN_EMAIL "$ADMIN_EMAIL"
fi

ADMIN_USER="${VAULT_ADMIN_USERNAME:-$(env_get VAULT_ADMIN_USERNAME)}"
ADMIN_USER="${ADMIN_USER:-admin}"
if [ -z "$(env_get VAULT_ADMIN_USERNAME)" ]; then
  env_set VAULT_ADMIN_USERNAME "$ADMIN_USER"
fi

CORS="$(env_get CORS_ALLOW_ORIGINS)"
if [ -z "$CORS" ]; then
  CORS="${CORS_ORIGINS:-[\"http://localhost:5173\"]}"
  env_set CORS_ALLOW_ORIGINS "$CORS"
fi

# ---------- 2. Build & start ----------

info "building images (first run takes several minutes)…"
$COMPOSE up -d --build

info "waiting for API health…"
for i in $(seq 1 60); do
  if curl -sf http://localhost:8000/api/v1/health/ready >/dev/null 2>&1; then
    info "API is up (ready)."
    break
  fi
  [ "$i" -eq 60 ] && { $COMPOSE logs --tail=40 api; die "API did not become healthy in 5 minutes. See logs above."; }
  sleep 5
done

# ---------- 3. HTTPS ----------

DOMAIN="${DOMAIN:-}"
CF_TUNNEL_TOKEN="${CF_TUNNEL_TOKEN:-}"

if [ -n "$CF_TUNNEL_TOKEN" ]; then
  info "configuring Cloudflare Tunnel…"
  if ! command -v cloudflared >/dev/null 2>&1; then
    ARCH="$(uname -m)"
    case "$ARCH" in
      aarch64|arm64) CF_ARCH=arm64 ;;
      *) CF_ARCH=amd64 ;;
    esac
    curl -sL "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-$CF_ARCH" \
      -o /usr/local/bin/cloudflared 2>/dev/null || die "cloudflared download failed"
    chmod +x /usr/local/bin/cloudflared
  fi
  cat >/etc/systemd/system/cloudflared.service <<EOF
[Unit]
Description=SecureVault Cloudflare Tunnel
After=network-online.target
Wants=network-online.target

[Service]
ExecStart=/usr/local/bin/cloudflared tunnel --token $CF_TUNNEL_TOKEN
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
  systemctl daemon-reload
  systemctl enable --now cloudflared
  PUBLIC_URL="https://<your-tunnel-hostname> (set hostname + origin http://localhost:8000 in Cloudflare dashboard)"

elif [ -n "$DOMAIN" ]; then
  info "configuring Caddy for $DOMAIN…"
  if ! command -v caddy >/dev/null 2>&1; then
    sudo apt-get update -qq
    sudo apt-get install -y -qq debian-keyring debian-archive-keyring apt-transport-https 2>/dev/null
    curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg 2>/dev/null
    curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | sudo tee /etc/apt/sources.list.d/caddy-stable.list >/dev/null
    sudo apt-get update -qq
    sudo apt-get install -y -qq caddy
  fi
  sudo tee /etc/caddy/Caddyfile >/dev/null <<EOF
$DOMAIN {
    reverse_proxy 127.0.0.1:8000
    header {
        Strict-Transport-Security "max-age=31536000"
    }
}
EOF
  sudo systemctl enable --now caddy
  PUBLIC_URL="https://$DOMAIN"
  warn "ensure your DNS A/AAAA record for $DOMAIN points at this VM's public IP"

else
  PUBLIC_URL="http://$(hostname -I | awk '{print $1}'):8000"
  warn "no DOMAIN or CF_TUNNEL_TOKEN set — serving plain HTTP on :8000."
  warn "production guards require HTTPS for Secure cookies; use a domain or tunnel."
fi

# ---------- 4. Backups & keep-alive ----------

BACKUP_DIR="$HOME/securevault-backups"
KEEP_DAYS="${STORAGE_KEEP_DAYS:-30}"
mkdir -p "$BACKUP_DIR"

BACKUP_SCRIPT="$ROOT/scripts/vault-backup.sh"
cat >"$BACKUP_SCRIPT" <<EOF
#!/usr/bin/env bash
set -euo pipefail
cd "$ROOT"
$COMPOSE exec -T db pg_dump -U postgres securevault | gzip > "$BACKUP_DIR/vault-\$(date +%F-%H%M).sql.gz"
find "$BACKUP_DIR" -name 'vault-*.sql.gz' -mtime +$KEEP_DAYS -delete
EOF
chmod +x "$BACKUP_SCRIPT"

(crontab -l 2>/dev/null | grep -v "vault-backup\|keep-alive" || true) >/tmp/crontab.new
echo "0 3 * * * $BACKUP_SCRIPT >> $BACKUP_DIR/cron.log 2>&1" >>/tmp/crontab.new
echo "0 * * * * logger -t securevault-keepalive alive >/dev/null 2>&1" >>/tmp/crontab.new
crontab /tmp/crontab.new
rm -f /tmp/crontab.new
info "installed nightly backup (kept $KEEP_DAYS days) + hourly keep-alive cron"

# ---------- 5. Summary ----------

ADMIN_PASS="$(env_get VAULT_ADMIN_PASSWORD)"
POSTGRES_PASS="$(env_get POSTGRES_PASSWORD)"

cat <<EOF

${c_bold}SecureVault deployment complete${c_reset}
────────────────────────────────────────────
URL:                $PUBLIC_URL
API health:         $PUBLIC_URL/api/v1/health/ready
Bootstrap admin:    $ADMIN_USER / $ADMIN_EMAIL
Admin password:     ${c_yellow}$ADMIN_PASS${c_reset}   ← save this now
Postgres password:  $POSTGRES_PASS   (in .env)
Backups:            $BACKUP_DIR (daily, $KEEP_DAYS days)

${c_bold}Next steps:${c_reset}
  1. Log in as the admin and enroll TOTP immediately (Admin/Auditor
     endpoints are blocked without it).
  2. Build the frontend (\`npm run build\`) and upload frontend/dist/
     to Cloudflare Pages / Vercel. Add an /api rewrites rule pointing
     back to $PUBLIC_URL, and set CORS_ALLOW_ORIGINS in .env to the
     frontend origin, then: $COMPOSE up -d --force-recreate api
  3. Test a backup restore: zcat $BACKUP_DIR/vault-*.gz | $COMPOSE exec -T db psql -U postgres securevault
EOF

if [ -n "$CF_TUNNEL_TOKEN" ] || [ -n "$DOMAIN" ]; then
  printf "\n${c_green}[ok]${c_reset} HTTPS is live; Secure cookies enabled.\n"
fi