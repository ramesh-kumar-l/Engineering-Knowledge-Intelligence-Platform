"""DocumentEnrichment ORM model — the per-document result of the processing pipeline.

One row per :class:`~app.models.document.Document` (1:1). ``source_content_hash``
records which version of the source document was processed, so a later sync that
changes the document marks this enrichment stale and eligible for reprocessing.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.enums import DocumentCategory, ProcessingStatus
from app.models.base import Base, TimestampMixin, UUIDMixin


class DocumentEnrichment(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "document_enrichments"
    __table_args__ = (
        UniqueConstraint("document_id", name="uq_enrichment_document"),
    )

    tenant_id: Mapped[str] = mapped_column(String(128), index=True)
    document_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("documents.id"), index=True
    )
    # The document content hash that this enrichment was computed from.
    source_content_hash: Mapped[str] = mapped_column(String(64))
    status: Mapped[ProcessingStatus] = mapped_column(
        String(16), default=ProcessingStatus.PROCESSED
    )
    category: Mapped[DocumentCategory] = mapped_column(
        String(16), default=DocumentCategory.OTHER
    )
    summary: Mapped[str] = mapped_column(Text, default="")
    keywords: Mapped[list[str]] = mapped_column(JSON, default=list)
    language: Mapped[str | None] = mapped_column(String(16), default=None)

    word_count: Mapped[int] = mapped_column(Integer, default=0)
    char_count: Mapped[int] = mapped_column(Integer, default=0)
    chunk_count: Mapped[int] = mapped_column(Integer, default=0)

    error: Mapped[str | None] = mapped_column(Text, default=None)
    processed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=None
    )
    extra: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
