"""Embedding ORM models — index runs, events and per-document state (Phase 4).

The vectors themselves live in Qdrant; these PostgreSQL rows are the operational record
of each embedding pass (counters, status, logs) and the staleness ledger that lets a
re-run embed only new/changed documents. ``DocumentEmbeddingState.source_content_hash``
mirrors the enrichment staleness pattern: it tracks the document content hash that was
last embedded. Run lifecycle and log levels reuse the shared sync enums.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.enums import SyncEventLevel, SyncStatus
from app.models.base import Base, TimestampMixin, UUIDMixin, _now


class EmbeddingRun(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "embedding_runs"

    tenant_id: Mapped[str] = mapped_column(String(128), index=True)
    status: Mapped[SyncStatus] = mapped_column(String(16), default=SyncStatus.RUNNING)

    documents_seen: Mapped[int] = mapped_column(Integer, default=0)
    documents_embedded: Mapped[int] = mapped_column(Integer, default=0)
    documents_skipped: Mapped[int] = mapped_column(Integer, default=0)
    chunk_count: Mapped[int] = mapped_column(Integer, default=0)
    failed_count: Mapped[int] = mapped_column(Integer, default=0)

    error: Mapped[str | None] = mapped_column(Text, default=None)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=None
    )


class EmbeddingEvent(UUIDMixin, Base):
    __tablename__ = "embedding_events"

    embedding_run_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("embedding_runs.id"), index=True
    )
    tenant_id: Mapped[str] = mapped_column(String(128), index=True)
    level: Mapped[SyncEventLevel] = mapped_column(String(16), default=SyncEventLevel.INFO)
    message: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class DocumentEmbeddingState(UUIDMixin, Base):
    __tablename__ = "document_embedding_state"
    __table_args__ = (
        UniqueConstraint("tenant_id", "document_id", name="uq_embedding_state_document"),
    )

    tenant_id: Mapped[str] = mapped_column(String(128), index=True)
    document_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("documents.id"), index=True
    )
    # Document content hash last embedded; a mismatch means re-embed.
    source_content_hash: Mapped[str] = mapped_column(String(64))
    chunk_count: Mapped[int] = mapped_column(Integer, default=0)
    model: Mapped[str] = mapped_column(String(64))
    embedded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
