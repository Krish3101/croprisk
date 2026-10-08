"""App setup: startup checks, host and routing config, health route."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app import routes
from app.config import settings
from app.db import engine, init_db


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # httpx logs full URLs at INFO, and the OpenWeather key is a query parameter.
    logging.basicConfig(
        level=settings.LOG_LEVEL,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)

    settings.log_optional_keys_status()
    init_db(engine)

    try:
        yield
    finally:
        engine.dispose()


app = FastAPI(
    title="CropRisk API",
    description="Crop- and growth-stage-aware risk assessment engine",
    version="0.1.0",
    lifespan=lifespan,
)


app.include_router(routes.router, prefix="/api")


@app.get("/api/health", tags=["health"])
def health_check() -> dict:
    return {"status": "ok"}
