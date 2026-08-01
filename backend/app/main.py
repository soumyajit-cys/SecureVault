from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.startup import (
    initialize_security_data,
)
from app.core.security_settings import (
    validate_security_settings
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
)

app.include_router(
    api_router,
    prefix=settings.API_V1_PREFIX,
)


