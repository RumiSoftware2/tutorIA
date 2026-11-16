from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    api_prefix: str = "/api/v1"
    cors_origins: str = "http://localhost:5173"
    database_url: str | None = None
    teacher_access_code: str | None = None
    jwt_secret_key: str | None = None
    jwt_expire_hours: int = Field(default=8, gt=0, le=168)

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def allowed_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
