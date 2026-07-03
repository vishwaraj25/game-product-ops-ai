from functools import cached_property

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Product Ops AI API"
    app_version: str = "0.1.0"
    database_url: str = Field(
        default="postgresql+psycopg://game_ops:game_ops_password@localhost:5432/game_product_ops",
        alias="DATABASE_URL",
    )
    backend_cors_origins: str = Field(
        default="http://localhost:3000",
        alias="BACKEND_CORS_ORIGINS",
    )
    ai_provider: str = Field(default="deterministic", alias="AI_PROVIDER")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @cached_property
    def cors_origins(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.backend_cors_origins.split(",")
            if origin.strip()
        ]


settings = Settings()
