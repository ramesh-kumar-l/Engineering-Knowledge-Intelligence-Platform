"""Embedding run + stats API schemas (mirrored in packages/contracts)."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel

from app.domain.enums import SyncEventLevel, SyncStatus
from app.models.embedding import EmbeddingEvent, EmbeddingRun


class EmbeddingTriggerRequest(BaseModel):
    """Optional scope for an embedding run. ``force`` re-embeds even unchanged docs."""

    force: bool = False


class EmbeddingRunOut(BaseModel):
    id: uuid.UUID
    status: SyncStatus
    documents_seen: int
    documents_embedded: int
    documents_skipped: int
    chunk_count: int
    failed_count: int
    error: str | None
    started_at: datetime
    finished_at: datetime | None

    @classmethod
    def from_model(cls, model: EmbeddingRun) -> EmbeddingRunOut:
        return cls(
            id=model.id,
            status=model.status,
            documents_seen=model.documents_seen,
            documents_embedded=model.documents_embedded,
            documents_skipped=model.documents_skipped,
            chunk_count=model.chunk_count,
            failed_count=model.failed_count,
            error=model.error,
            started_at=model.started_at,
            finished_at=model.finished_at,
        )


class EmbeddingRunListResponse(BaseModel):
    runs: list[EmbeddingRunOut]


class EmbeddingEventOut(BaseModel):
    id: uuid.UUID
    level: SyncEventLevel
    message: str
    created_at: datetime

    @classmethod
    def from_model(cls, model: EmbeddingEvent) -> EmbeddingEventOut:
        return cls(
            id=model.id,
            level=model.level,
            message=model.message,
            created_at=model.created_at,
        )


class EmbeddingEventListResponse(BaseModel):
    events: list[EmbeddingEventOut]


class EmbeddingStatsResponse(BaseModel):
    """Index coverage for the Search Explorer header."""

    documents_embedded: int
    vectors: int
    model: str
    dimension: int
