"""Connector service — validation, secret encryption, and lifecycle.

Validates a new connector against the source-type catalog, encrypts its credential
at rest (ADR-0008), and persists it. Only implemented source types can be created;
planned ones are catalog entries until their connector lands.
"""

from __future__ import annotations

import uuid
from typing import Any

from app.connectors import registry
from app.connectors.catalog import get_spec
from app.core.crypto import SecretBox
from app.domain.enums import SourceType
from app.models.connector import Connector
from app.repositories.connectors import ConnectorRepository


class ConnectorValidationError(ValueError):
    """Raised when a connector configuration is invalid (maps to HTTP 422)."""


class ConnectorService:
    def __init__(self, repo: ConnectorRepository, secret_box: SecretBox) -> None:
        self._repo = repo
        self._secret_box = secret_box

    async def create(
        self,
        tenant_id: str,
        source_type: SourceType,
        name: str,
        config: dict[str, Any],
        secret: str | None,
    ) -> Connector:
        if not registry.is_implemented(source_type):
            raise ConnectorValidationError(
                f"Source '{source_type.value}' is not available yet"
            )
        spec = get_spec(source_type)
        missing = [f.key for f in spec.config_fields if f.required and not config.get(f.key)]
        if missing:
            raise ConnectorValidationError(f"Missing config fields: {', '.join(missing)}")
        if spec.secret_label and not secret:
            raise ConnectorValidationError(f"{spec.secret_label} is required")

        connector = Connector(
            tenant_id=tenant_id,
            source_type=source_type,
            name=name,
            config=config,
            encrypted_secret=self._secret_box.encrypt(secret) if secret else None,
        )
        return await self._repo.add(connector)

    async def list(self, tenant_id: str) -> list[Connector]:
        return await self._repo.list(tenant_id)

    async def get(self, tenant_id: str, connector_id: uuid.UUID) -> Connector | None:
        return await self._repo.get(tenant_id, connector_id)

    def decrypt_secret(self, connector: Connector) -> str | None:
        if connector.encrypted_secret is None:
            return None
        return self._secret_box.decrypt(connector.encrypted_secret)
