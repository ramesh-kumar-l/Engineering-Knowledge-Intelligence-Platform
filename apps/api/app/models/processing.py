"""Processing ORM models — one batch run of the processing pipeline and its events.

``ProcessingRun`` records counters + outcome for a run over a tenant's documents;
``ProcessingEvent`` holds the ordered log lines surfaced in the Processing Jobs UI.
Run lifecycle (running/succeeded/failed) and log levels reuse the shared sync enums.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.enums import SyncEventLevel, SyncStatus
from app.models.base import Base, TimestampMixin, UUIDMixin, _now


class ProcessingRun(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "processing_runs"

    tenant_id: Mapped[str] = mapped_column(String(128), index=True)
    # Optional scope: a single connector, or None for all of the tenant's documents.
    connector_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("connectors.id"), index=True, default=None
    )
    status: Mapped[SyncStatus] = mapped_column(String(16), default=SyncStatus.RUNNING)

    documents_seen: Mapped[int] = mapped_column(Integer, default=0)
    processed_count: Mapped[int] = mapped_column(Integer, default=0)
    chunk_count: Mapped[int] = mapped_column(Integer, default=0)
    failed_count: Mapped[int] = mapped_column(Integer, default=0)

    error: Mapped[str | None] = mapped_column(Text, default=None)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=None
    )


class ProcessingEvent(UUIDMixin, Base):
    __tablename__ = "processing_events"

    processing_run_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("processing_runs.id"), index=True
    )
    tenant_id: Mapped[str] = mapped_column(String(128), index=True)
    level: Mapped[SyncEventLevel] = mapped_column(String(16), default=SyncEventLevel.INFO)
    message: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
