from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    GATEWAY_ALLOWED_ORIGINS: str = ""


    class Config:
        env_file = ".env"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings: Settings = get_settings()