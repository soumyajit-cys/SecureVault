from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi import Request
from fastapi.middleware.cors import (
    CORSMiddleware,
)
from fastapi.responses import JSONResponse

from app.core.startup import (
    initialize_security_data,
)
from app.core.exceptions import (
    AuthenticationError,
    AuthorizationError,
    SecureVaultException,
)
from app.core.security_settings import (
    validate_security_settings
)
from app.core.middleware import (
    RateLimitMiddleware,
    RequestIDMiddleware,
    RequestLoggingMiddleware,
    SecurityHeadersMiddleware,
)


from app.api.router import api_router
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.services.storage.garbage_collector import (
    CleanupTask,
    GarbageCollector,
)
from app.services.storage.storage_service import (
    StorageService,
)
from app.infrastructure.repositories.stored_file_repository import (
    SQLAlchemyStoredFileRepository,
)

settings = get_settings()

_cleanup_task: CleanupTask | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):

    global _cleanup_task

    configure_logging()

    validate_security_settings()
    initialize_security_data()

    if settings.GARBAGE_COLLECTION_ENABLED:

        from app.core.database import SessionLocal

        db = SessionLocal()

        try:

            collector = GarbageCollector(
                storage=StorageService(),
                stored_files=(
                    SQLAlchemyStoredFileRepository(db)
                ),
            )

            _cleanup_task = CleanupTask(
                collector
            )

            _cleanup_task.start()

        finally:

            db.close()

    yield

    if _cleanup_task is not None:

        await _cleanup_task.stop()

        _cleanup_task = None

app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    lifespan=lifespan,
    docs_url=(
        "/docs"
        if settings.APP_ENV != "production"
        else None
    ),
    redoc_url=(
        "/redoc"
        if settings.APP_ENV != "production"
        else None
    ),
    openapi_url=(
        "/openapi.json"
        if settings.APP_ENV != "production"
        else None
    ),
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=(
        settings.CORS_ALLOW_ORIGINS
    ),
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=[
        "GET",
        "POST",
        "PUT",
        "PATCH",
        "DELETE",
        "OPTIONS",
    ],
    allow_headers=[
        "Authorization",
        "Content-Type",
        "X-Request-ID",
    ],
)

if settings.ENABLE_SECURITY_HEADERS:
    app.add_middleware(
        SecurityHeadersMiddleware
    )

if settings.RATE_LIMIT_ENABLED:
    app.add_middleware(
        RateLimitMiddleware,
        general_limit=settings.RATE_LIMIT_PER_MINUTE,
        login_limit=settings.RATE_LIMIT_LOGIN_PER_MINUTE,
    )

app.add_middleware(
    RequestLoggingMiddleware
)

app.add_middleware(
    RequestIDMiddleware
)


@app.exception_handler(
    SecureVaultException
)
async def securevault_exception_handler(
    request: Request,
    exc: SecureVaultException,
):

    from app.crypto.exceptions import CryptoException
    from app.core.exceptions import ConflictError
    from app.core.exceptions import (
        LoginRateLimitedError,
        QuotaExceededError,
    )

    if isinstance(
        exc,
        LoginRateLimitedError,
    ):
        status_code = 429

    elif isinstance(
        exc,
        QuotaExceededError,
    ):
        status_code = 413

    elif isinstance(exc, AuthenticationError):
        status_code = 401

    elif isinstance(exc, AuthorizationError):
        status_code = 403

    elif isinstance(exc, CryptoException):
        status_code = 400

    elif isinstance(exc, ConflictError):
        status_code = 409

    else:
        status_code = 400

    return JSONResponse(
        status_code=status_code,
        content={
            "detail": str(exc)
        },
    )


app.include_router(
    api_router,
    prefix=settings.API_V1_PREFIX,
)


