from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Annotated

from pydantic import AliasChoices, Field, field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

ROOT_ENV_FILE = Path(__file__).resolve().parents[3] / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(str(ROOT_ENV_FILE), ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: str = "development"
    app_name: str = "Aegis OS"
    api_v1_prefix: str = "/api/v1"
    debug: str | bool = False
    log_level: str = "INFO"
    frontend_origin: str = "http://localhost:3000"

    database_url: str = Field(
        default="postgresql+psycopg://postgres:postgres@localhost:5432/aegis_os"
    )
    postgres_server: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "aegis_os"
    postgres_user: str = "postgres"
    postgres_password: str = "postgres"
    cloud_sql_connection_name: str | None = None
    cloud_sql_use_connector: bool = False
    allow_demo_fallback: bool = False

    google_cloud_project: str | None = None
    google_cloud_location: str = "us-central1"
    google_genai_model: str = "gemini-2.5-flash"
    google_genai_api_key: str | None = Field(
        default=None,
        validation_alias=AliasChoices("GOOGLE_GENAI_API_KEY", "GEMINI_API_KEY"),
    )
    gcs_bucket_name: str | None = None
    gcs_signed_url_ttl_seconds: int = 900

    max_upload_size_mb: int = 20
    allowed_upload_mime_types: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: [
            "application/pdf",
            "image/jpeg",
            "image/png",
            "image/webp",
            "text/plain",
        ]
    )

    @field_validator("allowed_upload_mime_types", mode="before")
    @classmethod
    def parse_mime_types(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @field_validator("debug", "cloud_sql_use_connector", "allow_demo_fallback", mode="before")
    @classmethod
    def parse_booleanish(cls, value: str | bool) -> bool:
        if isinstance(value, bool):
            return value
        normalized = value.strip().lower()
        if normalized in {"1", "true", "yes", "on"}:
            return True
        if normalized in {"0", "false", "no", "off", "release", "prod", "production"}:
            return False
        raise ValueError(f"Unsupported boolean value: {value}")

    @model_validator(mode="after")
    def validate_settings(self) -> "Settings":
        if self.max_upload_size_mb <= 0:
            raise ValueError("MAX_UPLOAD_SIZE_MB must be positive.")
        if self.cloud_sql_use_connector and not self.cloud_sql_connection_name:
            raise ValueError("CLOUD_SQL_CONNECTION_NAME is required when connector mode is enabled.")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
