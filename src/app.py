# Database
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
import src.models as models

# FastAPI stuff
from fastapi import FastAPI, Request
from src.settings import settings
from contextlib import asynccontextmanager

# Logging
import structlog
import time
from src.utils import logger

# Routes
from src.routes.auth import router as auth_router


@asynccontextmanager
async def lifecycle(app: FastAPI):
    client = AsyncIOMotorClient(settings.MONGODB_URI)
    await init_beanie(
        database=client.get_database("tycoon-db-dev"),
        document_models=[models.User],
    )
    try:
        logger.info("app-start")
        yield
    finally:
        client.close()
        logger.info("app-stop")


app = FastAPI(
    title="Tycoon API",
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    },
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    version="0.1.0",
    lifespan=lifecycle,  # type: ignore
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger = structlog.get_logger("tycoon-api")
    start_time = time.time()

    if not request.client:
        logger.info(
            "Request received",
            method=request.method,
            url=str(request.url),
            client_ip="unknown",
        )
    else:
        logger.info(
            "Request received",
            method=request.method,
            url=str(request.url),
            client_ip=request.client.host,
        )

    response = await call_next(request)

    duration = time.time() - start_time
    logger.info(
        "Request processed",
        method=request.method,
        url=str(request.url),
        status_code=response.status_code,
        duration=f"{duration:.2f}s",
    )
    return response


app.include_router(auth_router)
