"""Chunk ORM model — a retrievable unit of a processed document (Phase 2).

Chunks are the output of parsing + chunking and the input to embedding/retrieval in
later phases. They are stored in PostgreSQL now; vectorization into Qdrant is deferred
to the Retrieval phase. Chunks for a document are replaced wholesale on reprocessing.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, UUIDMixin, _now


class Chunk(UUIDMixin, Base):
    __tablename__ = "chunks"

    tenant_id: Mapped[str] = mapped_column(String(128), index=True)
    document_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("documents.id"), index=True
    )
    # 0-based position of the chunk within its document.
    ordinal: Mapped[int] = mapped_column(Integer)
    content: Mapped[str] = mapped_column(Text)
    content_hash: Mapped[str] = mapped_column(String(64))
    char_count: Mapped[int] = mapped_column(Integer, default=0)
    token_estimate: Mapped[int] = mapped_column(Integer, default=0)
    chunk_metadata: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
