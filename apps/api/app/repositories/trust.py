"""Trust read model — joins a document to its processing + embedding state (Phase 5).

One tenant-scoped query gives the trust layer everything it needs for a document's
confidence and freshness: provenance (``Document``), whether it was processed
(``DocumentEnrichment``) and whether it was embedded (``DocumentEmbeddingState``).
Outer joins keep documents that are not yet processed/embedded visible (with a
correspondingly lower confidence), so coverage gaps are surfaced rather than hidden.
"""

from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.enums import SourceType
from app.models.document import Document
from app.models.embedding import DocumentEmbeddingState
from app.models.enrichment import DocumentEnrichment

TrustRow = tuple[Document, DocumentEnrichment | None, DocumentEmbeddingState | None]


class TrustRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_document(
        self, tenant_id: str, document_id: uuid.UUID
    ) -> TrustRow | None:
        stmt = (
            select(Document, DocumentEnrichment, DocumentEmbeddingState)
            .outerjoin(
                DocumentEnrichment, DocumentEnrichment.document_id == Document.id
            )
            .outerjoin(
                DocumentEmbeddingState,
                DocumentEmbeddingState.document_id == Document.id,
            )
            .where(
                Document.id == document_id,
                Document.tenant_id == tenant_id,
                Document.is_deleted.is_(False),
            )
        )
        row = (await self._session.execute(stmt)).first()
        if row is None:
            return None
        return (row[0], row[1], row[2])

    async def list_documents(
        self,
        tenant_id: str,
        source_type: SourceType | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[TrustRow]:
        # Portable "most recently known activity first": coalesce avoids NULLS LAST,
        # which is not supported uniformly across PostgreSQL and SQLite.
        recency = func.coalesce(Document.source_updated_at, Document.updated_at)
        stmt = (
            select(Document, DocumentEnrichment, DocumentEmbeddingState)
            .outerjoin(
                DocumentEnrichment, DocumentEnrichment.document_id == Document.id
            )
            .outerjoin(
                DocumentEmbeddingState,
                DocumentEmbeddingState.document_id == Document.id,
            )
            .where(
                Document.tenant_id == tenant_id,
                Document.is_deleted.is_(False),
            )
        )
        if source_type is not None:
            stmt = stmt.where(Document.source_type == source_type)
        stmt = stmt.order_by(recency.desc()).limit(limit).offset(offset)
        rows = (await self._session.execute(stmt)).all()
        return [(r[0], r[1], r[2]) for r in rows]
