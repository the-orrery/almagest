from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置: env > .env > 默认值。"""

    model_config = SettingsConfigDict(
        env_prefix="ALMAGEST_", env_file=".env", extra="ignore"
    )

    debug: bool = False


settings = Settings()
