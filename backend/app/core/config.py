import os
from pathlib import Path
from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent.parent.parent

class Settings(BaseSettings):
    PROJECT_NAME: str = "Smallholder Agricultural Advisory System"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite+aiosqlite:///{BASE_DIR}/agri_advisory.db")
    USE_PGVECTOR: bool = os.getenv("USE_PGVECTOR", "false").lower() == "true"
    
    # Weather
    OPEN_METEO_BASE_URL: str = "https://api.open-meteo.com/v1/forecast"
    WEATHER_CACHE_TTL_SECONDS: int = 3600
    
    # Telephony
    TELEPHONY_AUTH_TOKEN: str = os.getenv("TELEPHONY_AUTH_TOKEN", "test-telephony-secret-token-2026")
    DEFAULT_IVR_LANGUAGE: str = "hi"
    
    # Security
    ALLOWED_HOSTS: list[str] = ["*"]
    CORS_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
        "*"
    ]
    
    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
