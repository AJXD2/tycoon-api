from motor.motor_asyncio import AsyncIOMotorClient

from beanie import init_beanie
from fastapi import FastAPI
from src.settings import settings
from contextlib import asynccontextmanager
from src.routes.auth import router as auth_router
import src.models as models


@asynccontextmanager
async def lifecycle(app: FastAPI):
    client = AsyncIOMotorClient(settings.MONGODB_URI)
    await init_beanie(
        database=client.get_database("tycoon-db-dev"),
        document_models=[models.User],
    )
    try:
        yield
    finally:
        client.close()


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

app.include_router(auth_router)
