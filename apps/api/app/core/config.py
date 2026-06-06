"""Application configuration — environment-driven (ADR-0006: no secrets in repo).

All settings load from environment variables prefixed ``EKIP_`` or a local ``.env``
file. Typed via pydantic-settings so configuration errors fail fast at startup.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

Environment = Literal["development", "staging", "production"]


class Settings(BaseSettings):
    """Typed application settings, validated at startup."""

    model_config = SettingsConfigDict(
        env_prefix="EKIP_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    env: Environment = "development"
    log_level: str = "INFO"

    # Datastores (ADR-0004).
    postgres_dsn: str = "postgresql+asyncpg://ekip:ekip@localhost:5432/ekip"
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "ekip-dev-password"
    qdrant_url: str = "http://localhost:6333"

    # CORS origins for the web app, comma-separated in the env var.
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])

    @property
    def is_production(self) -> bool:
        return self.env == "production"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Cached settings singleton. Use as a FastAPI dependency."""
    return Settings()
