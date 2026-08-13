#!/usr/bin/env bash
#
# package.sh — build a clean release archive for
# SecureVault.
#
# Excludes runtime data, caches, coverage, build
# artifacts and secrets so the shipped zip contains
# exactly what a deployment needs.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT_DIR="${1:-$ROOT/release}"
NAME="securevault-$(date +%Y%m%d-%H%M%S)"
STAGE="$(mktemp -d)"

trap 'rm -rf "$STAGE"' EXIT

echo "Staging clean tree at $STAGE/$NAME"
mkdir -p "$STAGE/$NAME"
cp -R "$ROOT/backend" "$ROOT/frontend" "$ROOT/docs" "$STAGE/$NAME/"
cp "$ROOT"/Dockerfile "$ROOT"/docker-compose.yml "$ROOT"/README.md \
   "$ROOT"/.env.example "$STAGE/$NAME/"

echo "Removing runtime/cache/artifact directories…"

# Python caches, coverage, test DBs, runtime storage
find "$STAGE/$NAME" -type d -name __pycache__ -prune -exec rm -rf {} +
find "$STAGE/$NAME" -type d -name .pytest_cache -prune -exec rm -rf {} +
find "$STAGE/$NAME" -type f -name "*.pyc" -delete
rm -rf "$STAGE/$NAME/backend/storage"
rm -rf "$STAGE/$NAME/backend/.coverage"

# Frontend build outputs & TS project files
rm -rf "$STAGE/$NAME/frontend/dist"
rm -rf "$STAGE/$NAME/frontend/node_modules"
find "$STAGE/$NAME" -type f -name "*.tsbuildinfo" -delete
find "$STAGE/$NAME" -type f -name "vite.config.js" -delete

# Never ship secrets
rm -f "$STAGE/$NAME/backend/.env"

mkdir -p "$OUT_DIR"

cd "$STAGE"
zip -qr "$OUT_DIR/$NAME.zip" "$NAME"

echo "Created $OUT_DIR/$NAME.zip"

cd "$ROOT"
unzip -l "$OUT_DIR/$NAME.zip" \
  | grep -E "storage/|.pytest_cache|.coverage|dist/|.env$|tsbuildinfo" \
  || echo "OK: no forbidden artifacts in archive"