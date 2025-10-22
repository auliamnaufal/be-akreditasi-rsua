from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        protected_namespaces=("settings_",),
    )

    app_name: str = Field(default="RSUA Incident Service")
    environment: str = Field(default="development")
    database_url: str = Field(default="mysql+mysqlconnector://user:password@db:3306/akreditasi")
    jwt_secret_key: str = Field(default="change-me")
    jwt_refresh_secret_key: str = Field(default="change-me-refresh")
    jwt_algorithm: str = Field(default="HS256")
    access_token_expires_minutes: int = Field(default=30)
    refresh_token_expires_minutes: int = Field(default=60 * 24 * 7)
    password_hashing_scheme: str = Field(default="bcrypt")
    token_version: int = Field(default=1)
    model_path: str = Field(default="models/incident_classifier.pkl")
    model_fallback_version: str = Field(default="fallback-rule-0.1")


@lru_cache
def get_settings() -> Settings:
    return Settings()
