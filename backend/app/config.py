import logging
from pathlib import Path

from pydantic import AliasChoices, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent

logger = logging.getLogger("croprisk")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(str(BACKEND_DIR / ".env"), ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    JWT_SECRET: str = Field(
        default="",
        validation_alias=AliasChoices("JWT_SECRET", "SECRET_KEY"),
    )
    OPENWEATHER_API_KEY: str = Field(
        default="",
        validation_alias=AliasChoices("OPENWEATHER_API_KEY", "OPENWEATHER_KEY", "OPENWEATHERMAP_API_KEY"),
    )
    OPENROUTER_API_KEY: str = Field(
        default="",
        validation_alias=AliasChoices("OPENROUTER_API_KEY", "OPENROUTER_KEY"),
    )
    DATABASE_URL: str = Field(
        default=f"sqlite:///{BACKEND_DIR / 'croprisk.db'}",
        validation_alias=AliasChoices("DATABASE_URL"),
    )
    LLM_MODEL: str = "google/gemini-2.0-flash-lite-preview-02-05:free"

    @field_validator("JWT_SECRET")
    @classmethod
    def validate_jwt_secret(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("JWT_SECRET must be set and non-empty.")
        return v.strip()

    def log_optional_keys_status(self) -> None:
        if not self.OPENWEATHER_API_KEY:
            logger.warning("OPENWEATHER_API_KEY is unset; geocoding and live forecasts will return 503.")
        if not self.OPENROUTER_API_KEY:
            logger.warning("OPENROUTER_API_KEY is unset; advisories will always use deterministic fallback.")


settings = Settings()
