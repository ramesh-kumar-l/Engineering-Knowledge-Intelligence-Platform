"""Graph-build ORM models — one projection run and its events (Phase 3).

The graph itself lives in Neo4j; these PostgreSQL rows are the operational record of
each build (counters, status, logs) surfaced in the Knowledge Graph jobs UI. Run
lifecycle and log levels reuse the shared sync enums (as the processing models do).
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.enums import SyncEventLevel, SyncStatus
from app.models.base import Base, TimestampMixin, UUIDMixin, _now


class GraphBuildRun(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "graph_build_runs"

    tenant_id: Mapped[str] = mapped_column(String(128), index=True)
    status: Mapped[SyncStatus] = mapped_column(String(16), default=SyncStatus.RUNNING)

    documents_seen: Mapped[int] = mapped_column(Integer, default=0)
    entity_count: Mapped[int] = mapped_column(Integer, default=0)
    relationship_count: Mapped[int] = mapped_column(Integer, default=0)

    error: Mapped[str | None] = mapped_column(Text, default=None)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=None
    )


class GraphBuildEvent(UUIDMixin, Base):
    __tablename__ = "graph_build_events"

    graph_build_run_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("graph_build_runs.id"), index=True
    )
    tenant_id: Mapped[str] = mapped_column(String(128), index=True)
    level: Mapped[SyncEventLevel] = mapped_column(String(16), default=SyncEventLevel.INFO)
    message: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
