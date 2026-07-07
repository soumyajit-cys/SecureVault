# SecureVault

Enterprise-grade encryption and secure file management platform.

## Current Phase

Phase 1:
- Clean Architecture foundation
- FastAPI
- PostgreSQL
- SQLAlchemy 2
- Alembic
- Health API
- Logging
- Configuration system

## Start

```bash
cp .env.example .env

pip install -r backend/requirements.txt

cd backend

uvicorn app.main:app --reload
```

Health Check:

http://localhost:8000/api/v1/health