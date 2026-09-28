FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libpq5 \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir -r /app/requirements.txt

COPY backend /app

RUN useradd --create-home --uid 10001 vault \
    && mkdir -p /app/storage \
    && chown -R vault:vault /app

USER vault

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --retries=5 \
    CMD python -c "import os, urllib.request; urllib.request.urlopen('http://localhost:' + os.environ.get('PORT', '8000') + '/api/v1/health/live')"

# Single worker: each uvicorn worker holds the full app (crypto, DB pool)
# at ~150-250 MB RSS, so --workers 1 is the only safe choice inside
# Render's 512 MB free tier. NOTE: raise workers only with more RAM
# (roughly one worker per 512 MB) AND Redis rate limiting
# (RATE_LIMIT_BACKEND=redis), which production startup enforces.
CMD ["sh", "-c", "alembic upgrade head && exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1"]
