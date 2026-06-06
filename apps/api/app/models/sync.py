"""Sync ORM models — one execution of a connector and its log events.

``SyncRun`` records counters + outcome for a sync; ``SyncEvent`` holds the ordered
log lines surfaced in the Sync Logs UI.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.enums import SyncEventLevel, SyncStatus
from app.models.base import Base, TimestampMixin, UUIDMixin, _now


class SyncRun(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "sync_runs"

    tenant_id: Mapped[str] = mapped_column(String(128), index=True)
    connector_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("connectors.id"), index=True
    )
    status: Mapped[SyncStatus] = mapped_column(String(16), default=SyncStatus.RUNNING)

    documents_seen: Mapped[int] = mapped_column(Integer, default=0)
    created_count: Mapped[int] = mapped_column(Integer, default=0)
    updated_count: Mapped[int] = mapped_column(Integer, default=0)
    unchanged_count: Mapped[int] = mapped_column(Integer, default=0)
    deleted_count: Mapped[int] = mapped_column(Integer, default=0)

    error: Mapped[str | None] = mapped_column(Text, default=None)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=None
    )


class SyncEvent(UUIDMixin, Base):
    __tablename__ = "sync_events"

    sync_run_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("sync_runs.id"), index=True
    )
    tenant_id: Mapped[str] = mapped_column(String(128), index=True)
    level: Mapped[SyncEventLevel] = mapped_column(String(16), default=SyncEventLevel.INFO)
    message: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
