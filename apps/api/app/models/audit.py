"""AuditEvent ORM model — persisted, queryable record of sensitive actions.

Replaces the Phase 0 log-only audit scaffold with a PostgreSQL-backed store
(security_requirements.md: auditability). Rows are append-only by convention.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, UUIDMixin, _now


class AuditEvent(UUIDMixin, Base):
    __tablename__ = "audit_events"

    tenant_id: Mapped[str] = mapped_column(String(128), index=True)
    actor: Mapped[str] = mapped_column(String(256))
    action: Mapped[str] = mapped_column(String(128))
    resource_type: Mapped[str] = mapped_column(String(64))
    resource_id: Mapped[str | None] = mapped_column(String(256), default=None)
    status: Mapped[str] = mapped_column(String(32), default="success")
    request_id: Mapped[str | None] = mapped_column(String(64), default=None)
    event_metadata: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
