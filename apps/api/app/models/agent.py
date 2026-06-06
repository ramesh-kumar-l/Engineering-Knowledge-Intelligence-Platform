"""AgentRun + AgentStep ORM models (Phase 8, ADR-0021).

Each agent execution is persisted: an ``AgentRun`` is the audit record (who ran which
agent, against what target, when, with what outcome) carrying a JSON snapshot of the
conclusions (headline, findings, actions, evidence with trust). Its ordered
``AgentStep`` rows are the execution trace shown in the Agent Execution Viewer. The
snapshot is faithful to run time even if the underlying corpus later changes.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.enums import AgentStepStatus, AgentType, SyncStatus
from app.models.base import Base, TimestampMixin, UUIDMixin, _now


class AgentRun(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "agent_runs"

    tenant_id: Mapped[str] = mapped_column(String(128), index=True)
    agent_type: Mapped[AgentType] = mapped_column(String(32))
    target: Mapped[str | None] = mapped_column(String(512), default=None)
    title: Mapped[str] = mapped_column(String(512))
    status: Mapped[SyncStatus] = mapped_column(String(16))
    confidence: Mapped[float | None] = mapped_column(Float, default=None)
    result_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, default=None)
    created_by: Mapped[str] = mapped_column(String(256))


class AgentStep(UUIDMixin, Base):
    __tablename__ = "agent_steps"

    run_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("agent_runs.id"), index=True)
    tenant_id: Mapped[str] = mapped_column(String(128), index=True)
    ordinal: Mapped[int] = mapped_column(Integer)
    name: Mapped[str] = mapped_column(String(128))
    status: Mapped[AgentStepStatus] = mapped_column(String(16))
    summary: Mapped[str] = mapped_column(Text)
    detail_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
