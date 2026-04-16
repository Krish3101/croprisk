"""Application Configuration
Settings, environment variables, and logging setup
"""

import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# Base directories
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"

# Create necessary directories
DATA_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)

# Load environment variables from .env file
env_path = BASE_DIR / ".env"
load_dotenv(dotenv_path=env_path)


# ==================== SETTINGS ====================


class Settings:
    """Application settings loaded from environment variables"""

    # API Keys
    OPENWEATHER_KEY: str | None = os.getenv("OPENWEATHER_KEY")
    OPENROUTER_API_KEY: str | None = os.getenv("OPENROUTER_API_KEY")
    INDIA_GOV_API_KEY: str | None = os.getenv(
        "INDIA_GOV_API_KEY", "579b464db66ec23bdd000001cdd3946e44ce4aad7209ff7b23ac571b"
    )

    # Server Configuration
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "9000"))
    ENV: str = os.getenv("ENV", "development")

    # LLM Configuration
    LLM_MODEL: str = os.getenv("LLM_MODEL", "openrouter/auto")
    LLM_TIMEOUT: int = int(os.getenv("LLM_TIMEOUT", "30"))

    # Cache Configuration
    WEATHER_CACHE_TTL: int = int(os.getenv("WEATHER_CACHE_TTL", "21600"))  # 6 hours
    PRICE_CACHE_TTL: int = int(os.getenv("PRICE_CACHE_TTL", "21600"))  # 6 hours

    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    # Authentication
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")

    # Application Defaults
    DEFAULT_CITY: str = os.getenv("DEFAULT_CITY", "Pune")
    DEFAULT_STATE: str = os.getenv("DEFAULT_STATE", "Maharashtra")
    DEFAULT_CROP: str = os.getenv("DEFAULT_CROP", "Tomato")

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = int(os.getenv("RATE_LIMIT_PER_MINUTE", "100"))
    RATE_LIMIT_CLEANUP_SIZE: int = int(os.getenv("RATE_LIMIT_CLEANUP_SIZE", "10000"))

    @classmethod
    def validate(cls):
        """Validate critical settings"""
        warnings = []

        if not cls.OPENWEATHER_KEY:
            warnings.append("OPENWEATHER_KEY not set - weather API will use local fallback data only")

        if not cls.OPENROUTER_API_KEY:
            warnings.append("OPENROUTER_API_KEY not set - AI chatbot will use mock responses only")

        if not cls.INDIA_GOV_API_KEY:
            warnings.append("INDIA_GOV_API_KEY not set - market prices may not be available")

        return warnings


# Singleton settings instance
settings = Settings()


def get_openrouter_headers() -> dict:
    """Get headers for OpenRouter API requests.

    Returns:
        A dictionary of headers including Authorization

    """
    key = settings.OPENROUTER_API_KEY
    if not key:
        return {}
    return {"Authorization": f"Bearer {key}", "HTTP-Referer": "http://localhost", "X-Title": "KisanAI"}


# ==================== LOGGING ====================


def setup_logging() -> None:
    """Configure application logging"""
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    # Create formatter
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S")

    # Console handler with UTF-8 encoding
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    if hasattr(console_handler.stream, "reconfigure"):
        try:
            console_handler.stream.reconfigure(encoding="utf-8")
        except Exception:
            pass

    # File handler with UTF-8 encoding
    file_handler = logging.FileHandler(LOGS_DIR / "kisanai.log", encoding="utf-8")
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

    # Suppress verbose third-party loggers
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)

    return root_logger


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance for a specific module

    Args:
        name: Module name (typically __name__)

    Returns:
        Configured logger instance

    """
    return logging.getLogger(name)


# Initialize logging on import
logger = setup_logging()

__all__ = [
    "settings",
    "get_openrouter_headers",
    "BASE_DIR",
    "DATA_DIR",
    "LOGS_DIR",
    "setup_logging",
    "get_logger",
    "logger",
]
