import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent

load_dotenv(BASE_DIR / ".env")

class Settings:
    PROJECT_NAME: str = "KisanAI Risk Intelligence"
    VERSION: str = "2.0.0"
    
    # Auth
    SECRET_KEY: str = os.getenv("SECRET_KEY", "default-insecure-key-change-it")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7 # 7 days
    
    # DB
    DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR}/kisanai_v2.db")
    
    # External APIs
    OPENWEATHER_KEY: str | None = os.getenv("OPENWEATHER_KEY")
    OPENROUTER_API_KEY: str | None = os.getenv("OPENROUTER_API_KEY")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "openrouter/auto")

settings = Settings()
