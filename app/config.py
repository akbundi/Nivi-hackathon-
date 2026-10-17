from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AI Reality Investigator API"
    database_url: str = "sqlite:///./data/investigator.db"
    storage_dir: Path = Path("./data/uploads")
    max_upload_bytes: int = Field(default=20 * 1024 * 1024, gt=0)
    allowed_media_types: tuple[str, ...] = (
        "image/jpeg",
        "image/png",
        "image/webp",
        "application/pdf",
    )

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
