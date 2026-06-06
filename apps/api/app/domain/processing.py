"""Processing run + job + stats API schemas (mirrored in packages/contracts)."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.domain.enums import SyncEventLevel, SyncStatus
from app.models.processing import ProcessingEvent, ProcessingRun


class ProcessingTriggerRequest(BaseModel):
    """Optional scope for a processing run. Empty body processes the whole tenant."""

    connector_id: uuid.UUID | None = None
    limit: int = Field(default=100, ge=1, le=1000)


class ProcessingRunOut(BaseModel):
    id: uuid.UUID
    connector_id: uuid.UUID | None
    status: SyncStatus
    documents_seen: int
    processed_count: int
    chunk_count: int
    failed_count: int
    error: str | None
    started_at: datetime
    finished_at: datetime | None

    @classmethod
    def from_model(cls, model: ProcessingRun) -> ProcessingRunOut:
        return cls(
            id=model.id,
            connector_id=model.connector_id,
            status=model.status,
            documents_seen=model.documents_seen,
            processed_count=model.processed_count,
            chunk_count=model.chunk_count,
            failed_count=model.failed_count,
            error=model.error,
            started_at=model.started_at,
            finished_at=model.finished_at,
        )


class ProcessingRunListResponse(BaseModel):
    runs: list[ProcessingRunOut]


class ProcessingEventOut(BaseModel):
    id: uuid.UUID
    level: SyncEventLevel
    message: str
    created_at: datetime

    @classmethod
    def from_model(cls, model: ProcessingEvent) -> ProcessingEventOut:
        return cls(
            id=model.id,
            level=model.level,
            message=model.message,
            created_at=model.created_at,
        )


class ProcessingEventListResponse(BaseModel):
    events: list[ProcessingEventOut]


class ChunkStatsResponse(BaseModel):
    """Aggregate processing statistics (Chunk Statistics screen)."""

    documents_processed: int
    total_chunks: int
    total_chunk_chars: int
    avg_chunks_per_document: float
    avg_chunk_chars: float
    category_distribution: dict[str, int]
