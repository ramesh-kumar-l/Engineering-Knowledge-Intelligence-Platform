"""Connector API schemas (mirrored in packages/contracts as TypeScript).

Secrets are write-only: a credential is accepted on create but never returned;
``has_secret`` reports presence only.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel

from app.connectors.base import ConnectorSpec
from app.domain.enums import ConnectorStatus, SourceType
from app.models.connector import Connector


class ConfigFieldInfo(BaseModel):
    key: str
    label: str
    required: bool


class SourceTypeInfo(BaseModel):
    """One source type in the Connector Catalog."""

    source_type: SourceType
    label: str
    description: str
    implemented: bool
    config_fields: list[ConfigFieldInfo]
    secret_label: str | None

    @classmethod
    def from_spec(cls, spec: ConnectorSpec) -> SourceTypeInfo:
        return cls(
            source_type=spec.source_type,
            label=spec.label,
            description=spec.description,
            implemented=spec.implemented,
            config_fields=[
                ConfigFieldInfo(key=f.key, label=f.label, required=f.required)
                for f in spec.config_fields
            ],
            secret_label=spec.secret_label,
        )


class ConnectorCatalogResponse(BaseModel):
    sources: list[SourceTypeInfo]


class ConnectorCreate(BaseModel):
    source_type: SourceType
    name: str
    config: dict[str, Any] = {}
    secret: str | None = None


class ConnectorOut(BaseModel):
    id: uuid.UUID
    source_type: SourceType
    name: str
    status: ConnectorStatus
    config: dict[str, Any]
    has_secret: bool
    cursor: str | None
    last_synced_at: datetime | None
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_model(cls, model: Connector) -> ConnectorOut:
        return cls(
            id=model.id,
            source_type=model.source_type,
            name=model.name,
            status=model.status,
            config=model.config,
            has_secret=model.encrypted_secret is not None,
            cursor=model.cursor,
            last_synced_at=model.last_synced_at,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )


class ConnectorListResponse(BaseModel):
    connectors: list[ConnectorOut]
