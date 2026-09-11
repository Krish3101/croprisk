"""FastAPI main application entrypoint."""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import settings
from app.db import Base, engine
from app.domain.crops import validate_catalogue
from app.errors import register_error_handlers
from app.routes import auth, lookup, plots, risk


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # 1. Assert crop catalogue integrity on startup (fails fast if invalid)
    validate_catalogue()

    # 2. Log configuration status for optional keys
    settings.log_optional_keys_status()

    # 3. Create database tables if they do not exist
    Base.metadata.create_all(bind=engine)

    yield


app = FastAPI(
    title="CropRisk API",
    description="Crop- and growth-stage-aware risk assessment engine",
    version="0.1.0",
    lifespan=lifespan,
)

register_error_handlers(app)

app.include_router(auth.router, prefix="/api")
app.include_router(lookup.router, prefix="/api")
app.include_router(plots.router, prefix="/api")
app.include_router(risk.router, prefix="/api")
