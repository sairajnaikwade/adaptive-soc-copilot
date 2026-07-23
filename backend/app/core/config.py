"""
Application configuration management.

Uses Pydantic BaseSettings to load all configuration from environment
variables and the .env file. A single `settings` singleton is imported
throughout the application to avoid redundant reads.
"""

from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Centralized application settings loaded from environment variables.

    All fields correspond directly to variables defined in .env.example.
    Pydantic validates types and raises a clear error on startup if any
    required variable is missing.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",  # Ignore unknown env vars silently
    )

    # -------------------------------------------------------------------------
    # Application metadata
    # -------------------------------------------------------------------------
    APP_NAME: str = "Adaptive SOC CoPilot"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False

    # -------------------------------------------------------------------------
    # Database
    # -------------------------------------------------------------------------
    DATABASE_URL: str  # Required — no default

    # -------------------------------------------------------------------------
    # Security & JWT
    # -------------------------------------------------------------------------
    SECRET_KEY: str  # Required — no default
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # -------------------------------------------------------------------------
    # CORS — stored as a comma-separated string, parsed as a list via property
    # -------------------------------------------------------------------------
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse the comma-separated CORS_ORIGINS string into a list."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    # -------------------------------------------------------------------------
    # Email (Gmail SMTP)
    # -------------------------------------------------------------------------
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = ""
    SMTP_FROM_NAME: str = "SOC CoPilot"
    EMAIL_ENABLED: bool = False

    # -------------------------------------------------------------------------
    # Machine Learning
    # -------------------------------------------------------------------------
    MODEL_STORAGE_PATH: str = "./ml_models"
    ISOLATION_FOREST_CONTAMINATION: float = 0.05
    RETRAIN_MIN_SAMPLES: int = 50

    # -------------------------------------------------------------------------
    # Convenience properties
    # -------------------------------------------------------------------------
    @property
    def is_development(self) -> bool:
        return self.ENVIRONMENT == "development"

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"

    @property
    def is_testing(self) -> bool:
        return self.ENVIRONMENT == "testing"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Return the cached Settings singleton.

    Uses lru_cache so settings are only parsed from environment once,
    regardless of how many modules import get_settings().
    """
    return Settings()


# Module-level singleton — imported directly by other modules
settings: Settings = get_settings()
