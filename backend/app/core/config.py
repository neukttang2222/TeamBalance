from functools import lru_cache
from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parents[2]
ENV_FILE = BASE_DIR / ".env"


class Settings(BaseSettings):
    app_name: str = "TeamBalance API"
    gemini_api_key: str
    gemini_model: str = "gemini-1.5-flash"
    supabase_db_url: str
    enable_runtime_schema_init: bool = True
    allowed_origins: list[str] = [
        "http://127.0.0.1:5500",
        "http://localhost:5500",
        "http://127.0.0.1:3000",
        "http://localhost:3000",
    ]

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def parse_allowed_origins(cls, value):
        if value is None or value == "":
            return [
                "http://127.0.0.1:5500",
                "http://localhost:5500",
                "http://127.0.0.1:3000",
                "http://localhost:3000",
            ]
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
