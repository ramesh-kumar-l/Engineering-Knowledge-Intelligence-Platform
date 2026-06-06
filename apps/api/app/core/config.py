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

    # Auth (ADR-0008). JWT bearer verification is the production security boundary.
    # Secrets MUST be injected via env in staging/production (defaults are dev-only).
    jwt_secret: str = "dev-insecure-jwt-secret-change-me"
    jwt_algorithm: str = "HS256"
    jwt_audience: str | None = None
    jwt_issuer: str | None = None
    # Dev-only header principal fallback; forced off in production regardless of value.
    dev_auth_enabled: bool = True

    # Symmetric key for encrypting connector secrets at rest (ADR-0008). Override in env.
    secret_key: str = "dev-insecure-secret-key-change-me"

    # Auto-create ORM schema on startup (dev convenience). Production uses migrations.
    auto_create_schema: bool = True

    @property
    def is_production(self) -> bool:
        return self.env == "production"

    @property
    def header_auth_allowed(self) -> bool:
        """Dev header principal is only honored outside production."""
        return self.dev_auth_enabled and not self.is_production


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Cached settings singleton. Use as a FastAPI dependency."""
    return Settings()
