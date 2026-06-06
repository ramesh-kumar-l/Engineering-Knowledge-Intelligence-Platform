"""Connector ORM model — a configured ingestion source (system of record).

Each row is one tenant-scoped source instance (e.g. a GitHub repo). Credentials are
stored encrypted (``encrypted_secret``), never in plaintext (ADR-0008).
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.enums import ConnectorStatus, SourceType
from app.models.base import Base, TimestampMixin, UUIDMixin


class Connector(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "connectors"

    tenant_id: Mapped[str] = mapped_column(String(128), index=True)
    source_type: Mapped[SourceType] = mapped_column(String(32))
    name: Mapped[str] = mapped_column(String(256))
    status: Mapped[ConnectorStatus] = mapped_column(
        String(16), default=ConnectorStatus.ACTIVE
    )
    # Non-secret source settings (repo owner/name, base url, …).
    config: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    # Encrypted credential (token/password). Nullable for sources needing no secret.
    encrypted_secret: Mapped[str | None] = mapped_column(String(1024), default=None)
    # Incremental-sync cursor (e.g. ISO timestamp of the last successful sync).
    cursor: Mapped[str | None] = mapped_column(String(256), default=None)
    last_synced_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=None
    )
