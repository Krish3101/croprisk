"""KisanAI FastAPI Application
Main entry point for the REST API server
"""

import time
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from config import get_logger, settings, setup_logging
from middleware.performance import PerformanceMonitoringMiddleware
from routes import auth, chatbot, crops, dashboard, expenses, prices, soil, weather

# Setup logging
setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle app lifespan events"""
    # Startup
    logger.info("KisanAI API starting up...")
    logger.info(f"Environment: {settings.ENV}")
    logger.info(
        f"API Keys configured: OpenWeather={bool(settings.OPENWEATHER_KEY)}, OpenRouter={bool(settings.OPENROUTER_API_KEY)}"
    )

    # Initialize database
    from models.database import init_db

    init_db()

    yield

    # Shutdown
    logger.info("KisanAI API shutting down...")


# Initialize FastAPI app
app = FastAPI(
    title="KisanAI API",
    description="Backend API for KisanAI Smart Farming Assistant",
    version="2.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan,
)

# CORS middleware (dev-friendly; restrict in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.ENV == "development" else ["http://localhost:9000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# GZip compression for responses > 1000 bytes
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Performance monitoring
app.add_middleware(PerformanceMonitoringMiddleware, slow_request_threshold=1.0)

# Thread-safe rate limiting middleware
from threading import Lock

request_counts = {}
rate_limit_lock = Lock()


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """Rate limiting based on configuration settings"""
    client_ip = request.client.host
    current_minute = int(time.time() / 60)

    key = f"{client_ip}:{current_minute}"

    with rate_limit_lock:
        # Clean old entries to prevent memory leak
        if len(request_counts) > settings.RATE_LIMIT_CLEANUP_SIZE:
            request_counts.clear()

        request_counts[key] = request_counts.get(key, 0) + 1
        current_count = request_counts[key]

    if current_count > settings.RATE_LIMIT_PER_MINUTE:
        return JSONResponse(status_code=429, content={"detail": "Rate limit exceeded. Please try again later."})

    response = await call_next(request)
    return response


# Include API routers
app.include_router(auth.router, prefix="/api/v1", tags=["Authentication"])
app.include_router(weather.router, prefix="/api/v1", tags=["Weather"])
app.include_router(prices.router, prefix="/api/v1", tags=["Prices"])
app.include_router(soil.router, prefix="/api/v1", tags=["Soil"])
app.include_router(crops.router, prefix="/api/v1", tags=["Crops"])
app.include_router(expenses.router, prefix="/api/v1", tags=["Expenses"])
app.include_router(chatbot.router, prefix="/api/v1", tags=["Chatbot"])
app.include_router(dashboard.router, prefix="/api/v1", tags=["Dashboard"])


# Global exception handlers
@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    """Handle Pydantic validation errors"""
    logger.warning(f"Validation error: {exc}")
    return JSONResponse(
        status_code=422,
        content={"detail": "Invalid request data", "errors": exc.errors()},
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions"""
    logger.error(f"Unhandled exception on {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected error occurred. Please try again later."},
    )


@app.get("/")
def home():
    """Health check endpoint."""
    return {"status": "KisanAI API server running", "version": "2.0", "type": "REST API", "environment": settings.ENV}


@app.get("/health")
def health_check():
    """Detailed health check endpoint."""
    import sys
    from datetime import datetime

    return {
        "status": "healthy",
        "version": "2.0",
        "timestamp": datetime.now().isoformat(),
        "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "environment": settings.ENV,
        "api_keys": {
            "openweather": bool(settings.OPENWEATHER_KEY),
            "openrouter": bool(settings.OPENROUTER_API_KEY),
            "india_gov": bool(settings.INDIA_GOV_API_KEY),
        },
        "services": {
            "weather": "operational",
            "prices": "operational" if settings.INDIA_GOV_API_KEY else "limited",
            "crops": "operational",
            "expenses": "operational",
            "chatbot": "operational" if settings.OPENROUTER_API_KEY else "limited",
        },
    }


if __name__ == "__main__":
    uvicorn.run("main:app", host=settings.HOST, port=settings.PORT, reload=(settings.ENV == "development"))
