"""App setup: startup checks, host and routing config, health route."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy import text
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.api import lookup, plots
from app.config import settings
from app.db import SCHEMA_VERSION, engine, init_db
from app.errors import register_error_handlers
from app.schemas import HealthResponse
from app.services.catalogue_loader import CATALOGUE_VERSION


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

    yield


app = FastAPI(
    title="CropRisk API",
    description="Crop- and growth-stage-aware risk assessment engine",
    version="0.1.0",
    lifespan=lifespan,
)

# No auth, so only accept local Host headers (blocks DNS rebinding).
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["127.0.0.1", "localhost", "*.localhost"],
)

register_error_handlers(app)

app.include_router(lookup.router, prefix="/api")
app.include_router(plots.router, prefix="/api")


@app.get("/api/health", response_model=HealthResponse, tags=["health"])
def health_check() -> HealthResponse:
    db_ok = False
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            db_ok = True
    except Exception:
        db_ok = False

    return HealthResponse(
        status="ok" if db_ok else "degraded",
        db=db_ok,
        weather_key=bool(settings.OPENWEATHER_API_KEY),
        llm_key=bool(settings.OPENROUTER_API_KEY),
        catalogue_version=CATALOGUE_VERSION,
        schema_version=SCHEMA_VERSION,
    )
