"""Sync run + event API schemas (mirrored in packages/contracts)."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel

from app.domain.enums import SyncEventLevel, SyncStatus
from app.models.sync import SyncEvent, SyncRun


class SyncRunOut(BaseModel):
    id: uuid.UUID
    connector_id: uuid.UUID
    status: SyncStatus
    documents_seen: int
    created_count: int
    updated_count: int
    unchanged_count: int
    deleted_count: int
    error: str | None
    started_at: datetime
    finished_at: datetime | None

    @classmethod
    def from_model(cls, model: SyncRun) -> SyncRunOut:
        return cls(
            id=model.id,
            connector_id=model.connector_id,
            status=model.status,
            documents_seen=model.documents_seen,
            created_count=model.created_count,
            updated_count=model.updated_count,
            unchanged_count=model.unchanged_count,
            deleted_count=model.deleted_count,
            error=model.error,
            started_at=model.started_at,
            finished_at=model.finished_at,
        )


class SyncRunListResponse(BaseModel):
    runs: list[SyncRunOut]


class SyncEventOut(BaseModel):
    id: uuid.UUID
    level: SyncEventLevel
    message: str
    created_at: datetime

    @classmethod
    def from_model(cls, model: SyncEvent) -> SyncEventOut:
        return cls(
            id=model.id,
            level=model.level,
            message=model.message,
            created_at=model.created_at,
        )


class SyncEventListResponse(BaseModel):
    events: list[SyncEventOut]
