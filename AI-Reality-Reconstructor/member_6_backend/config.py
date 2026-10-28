"""Backend-only environment configuration."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from sqlalchemy.engine import URL


BACKEND_DIR = Path(__file__).resolve().parent


def _int_env(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer") from exc


def _database_url() -> str | URL:
    """Build a SQLAlchemy URL from discrete DB settings without URI interpolation."""
    explicit_url = os.getenv("DATABASE_URL")
    if explicit_url:
        return explicit_url

    host = os.getenv("DB_HOST")
    if host:
        required = {
            "DB_NAME": os.getenv("DB_NAME"),
            "DB_USER": os.getenv("DB_USER"),
            "DB_PASSWORD": os.getenv("DB_PASSWORD"),
        }
        missing = [name for name, value in required.items() if not value]
        if missing:
            raise ValueError("Database configuration is incomplete: " + ", ".join(missing))
        port = _int_env("DB_PORT", 5432)
        if not 1 <= port <= 65535:
            raise ValueError("DB_PORT must be between 1 and 65535")
        return URL.create(
            drivername="postgresql+psycopg",
            username=required["DB_USER"],
            password=required["DB_PASSWORD"],
            host=host,
            port=port,
            database=required["DB_NAME"],
        )

    return f"sqlite:///{(BACKEND_DIR / 'data' / 'backend.db').as_posix()}"


@dataclass(frozen=True)
class Settings:
    database_url: str | URL = field(default_factory=_database_url)
    storage_dir: Path = Path(os.getenv("STORAGE_DIR", str(BACKEND_DIR / "data" / "evidence")))
    max_upload_bytes: int = _int_env("MAX_UPLOAD_BYTES", 25 * 1024 * 1024)
    allowed_extensions: frozenset[str] = frozenset(
        part.strip().lower().lstrip(".")
        for part in os.getenv("ALLOWED_EXTENSIONS", "pdf,txt,csv,json,png,jpg,jpeg,webp,mp4,mov,wav,mp3,docx").split(",")
        if part.strip()
    )
    adapter_mode: str = os.getenv("ADAPTER_MODE", "mock").strip().lower()
    real_adapter_factory: str | None = os.getenv("REAL_ADAPTER_FACTORY")
    processing_timeout_seconds: int = _int_env("PROCESSING_TIMEOUT_SECONDS", 300)
    cors_origins: tuple[str, ...] = tuple(
        item.strip() for item in os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:5173").split(",") if item.strip()
    )
    log_level: str = os.getenv("LOG_LEVEL", "INFO").upper()

    def __post_init__(self) -> None:
        if self.max_upload_bytes < 1:
            raise ValueError("MAX_UPLOAD_BYTES must be greater than zero")
        if self.processing_timeout_seconds < 1:
            raise ValueError("PROCESSING_TIMEOUT_SECONDS must be greater than zero")
        if self.adapter_mode not in {"mock", "real"}:
            raise ValueError("ADAPTER_MODE must be either 'mock' or 'real'")


settings = Settings()
