"""Conversation + Message ORM models (Phase 6, ADR-0019).

The assistant persists each conversation and its messages so engineers can revisit
prior answers (Conversation History) and the evidence behind them (Evidence Viewer).
An assistant message stores a JSON snapshot of its answer (summary, citations with
trust, related graph facts) as it stood when generated — a faithful record even if the
underlying corpus later changes.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.enums import AssistantIntent, MessageRole
from app.models.base import Base, TimestampMixin, UUIDMixin, _now


class Conversation(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "conversations"

    tenant_id: Mapped[str] = mapped_column(String(128), index=True)
    title: Mapped[str] = mapped_column(String(512))
    created_by: Mapped[str] = mapped_column(String(256))


class Message(UUIDMixin, Base):
    __tablename__ = "messages"

    conversation_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("conversations.id"), index=True
    )
    tenant_id: Mapped[str] = mapped_column(String(128), index=True)
    role: Mapped[MessageRole] = mapped_column(String(16))
    content: Mapped[str] = mapped_column(Text)
    # Assistant messages only: classified intent + overall trust + answer snapshot.
    intent: Mapped[AssistantIntent | None] = mapped_column(String(32), default=None)
    confidence: Mapped[float | None] = mapped_column(Float, default=None)
    answer_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
