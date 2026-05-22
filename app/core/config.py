"""Configuración central de la aplicación basada en variables de entorno."""
from functools import lru_cache
import re
from typing import List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # App
    APP_NAME: str = "PQRS API"
    APP_ENV: str = "development"
    APP_DEBUG: bool = True
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000

    # Seguridad
    SECRET_KEY: str = "change-me"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # CORS
    CORS_ORIGINS: str = "http://localhost:4200"

    # Base de datos
    DATABASE_URL: str = (
        "postgresql+psycopg2://pqrs_user:pqrs_pass@localhost:5432/pqrs_db"
    )

    # Superusuario inicial
    FIRST_ADMIN_EMAIL: str = "admin@pqrs.local"
    FIRST_ADMIN_PASSWORD: str = "Admin123*"
    FIRST_ADMIN_NAME: str = "Administrador"

    # SMTP
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = "no-reply@pqrs.local"
    SMTP_TLS: bool = True
    SMTP_ENABLED: bool = False

    # Notificaciones por área (varios correos separados por coma, punto y coma o espacio)
    CALIDAD_EMAILS: str = ""
    LOGISTICA_EMAILS: str = ""
    COMERCIAL_EMAILS: str = ""

    # Storage
    STORAGE_BACKEND: str = "local"  # local | s3
    UPLOAD_DIR: str = "app/uploads"
    MAX_UPLOAD_MB: int = 10

    # S3
    S3_BUCKET: str = ""
    S3_REGION: str = "us-east-1"
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    def _parse_email_list(self, raw: str) -> list[str]:
        return [email.strip() for email in re.split(r"[,;\s]+", raw) if email.strip()]

    def emails_for_area(self, area_codigo: str | None) -> list[str]:
        area = (area_codigo or "").strip().upper()
        if area == "CALIDAD":
            return self._parse_email_list(self.CALIDAD_EMAILS)
        if area in {"LOGISTICA", "LOGÍSTICA"}:
            return self._parse_email_list(self.LOGISTICA_EMAILS)
        if area == "COMERCIAL":
            return self._parse_email_list(self.COMERCIAL_EMAILS)
        return []

    @field_validator("APP_DEBUG", "SMTP_TLS", "SMTP_ENABLED", mode="before")
    @classmethod
    def _parse_bool(cls, v):
        if isinstance(v, bool):
            return v
        if isinstance(v, str):
            return v.strip().lower() in {"1", "true", "yes", "y", "on"}
        return bool(v)


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
