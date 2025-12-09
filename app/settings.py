from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Service URLs (required)
    AUTH_SERVICE_URL: str = Field(..., alias="AUTH_SERVICE_URL")
    DEPEX_SERVICE_URL: str = Field(..., alias="DEPEX_SERVICE_URL")
    VEXGEN_SERVICE_URL: str = Field(..., alias="VEXGEN_SERVICE_URL")

    # Application settings (safe defaults)
    DOCS_URL: str | None = Field(None, alias="DOCS_URL")
    GATEWAY_ALLOWED_ORIGINS: list[str] = Field(["*"], alias="GATEWAY_ALLOWED_ORIGINS")


@lru_cache
def get_settings() -> Settings:
    return Settings() # type: ignore[call-arg]


settings: Settings = get_settings()
