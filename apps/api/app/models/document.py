"""Document ORM model — an ingested knowledge artifact (system of record).

Change tracking is driven by ``content_hash``: an unchanged hash means the source
document did not change since the last sync. Raw content is retained for the Phase 2
processing/chunking layer. Provenance (source + timestamps) powers the trust layer.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.enums import SourceType
from app.models.base import Base, TimestampMixin, UUIDMixin


class Document(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "documents"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "connector_id", "external_id", name="uq_document_identity"
        ),
    )

    tenant_id: Mapped[str] = mapped_column(String(128), index=True)
    connector_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("connectors.id"), index=True
    )
    source_type: Mapped[SourceType] = mapped_column(String(32))
    # Stable id from the source system (issue number, page id, …).
    external_id: Mapped[str] = mapped_column(String(512))

    title: Mapped[str] = mapped_column(String(1024))
    url: Mapped[str | None] = mapped_column(String(2048), default=None)
    content_hash: Mapped[str] = mapped_column(String(64))
    raw_content: Mapped[str | None] = mapped_column(Text, default=None)
    doc_metadata: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    source_updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=None
    )
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
