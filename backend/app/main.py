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

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):

    configure_logging()

    validate_security_settings()
    initialize_security_data()

    yield

app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(
    api_router,
    prefix=settings.API_V1_PREFIX,
)


