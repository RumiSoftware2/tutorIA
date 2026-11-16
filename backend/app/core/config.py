from functools import lru_cache

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    api_prefix: str = "/api/v1"
    cors_origins: str = "http://localhost:5173"
    database_url: str | None = None
    teacher_access_code: str | None = None
    jwt_secret_key: str | None = None
    jwt_expire_hours: int = Field(default=8, gt=0, le=168)
    upload_max_mb: int = Field(default=10, ge=1, le=100)
    max_extracted_chars: int = Field(default=250_000, ge=1_000, le=1_000_000)
    chunk_size_chars: int = Field(default=1_200, ge=100, le=10_000)
    chunk_overlap_chars: int = Field(default=150, ge=0, le=2_000)

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @model_validator(mode="after")
    def validate_chunk_settings(self) -> "Settings":
        if self.chunk_overlap_chars >= self.chunk_size_chars:
            raise ValueError("CHUNK_OVERLAP_CHARS debe ser menor que CHUNK_SIZE_CHARS.")
        return self

    @property
    def allowed_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
