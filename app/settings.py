from functools import lru_cache

from pydantic import ConfigDict, Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = ConfigDict(env_file=".env")

    DOCS_URL: str | None = None
    GATEWAY_ALLOWED_ORIGINS: str = ""

    AUTH_SERVICE_URL: str = Field(default="http://securechain-auth:8000")
    DEPEX_SERVICE_URL: str = Field(default="http://securechain-depex:8000")
    VEXGEN_SERVICE_URL: str = Field(default="http://securechain-vexgen:8000")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings: Settings = get_settings()
