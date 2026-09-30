import logging
from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent

logger = logging.getLogger("croprisk")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(str(BACKEND_DIR / ".env"), ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    JWT_SECRET: str = ""
    OPENWEATHER_API_KEY: str = ""
    OPENROUTER_API_KEY: str = ""
    DATABASE_URL: str = f"sqlite:///{BACKEND_DIR / 'croprisk.db'}"

    @field_validator("JWT_SECRET")
    @classmethod
    def validate_jwt_secret(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("JWT_SECRET must be set and non-empty.")
        return v.strip()

    def log_optional_keys_status(self) -> None:
        if not self.OPENWEATHER_API_KEY:
            logger.warning(
                "OPENWEATHER_API_KEY is unset; geocoding and live forecasts will return 503."
            )
        if not self.OPENROUTER_API_KEY:
            logger.warning(
                "OPENROUTER_API_KEY is unset; advisories will always use deterministic fallback."
            )


settings = Settings()
