"""Document enrichment data access + processing aggregates (tenant-scoped)."""

from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.enums import DocumentCategory, ProcessingStatus
from app.models.document import Document
from app.models.enrichment import DocumentEnrichment


class EnrichmentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, enrichment: DocumentEnrichment) -> DocumentEnrichment:
        self._session.add(enrichment)
        await self._session.flush()
        return enrichment

    async def get_by_document(
        self, tenant_id: str, document_id: uuid.UUID
    ) -> DocumentEnrichment | None:
        stmt = select(DocumentEnrichment).where(
            DocumentEnrichment.tenant_id == tenant_id,
            DocumentEnrichment.document_id == document_id,
        )
        return (await self._session.execute(stmt)).scalar_one_or_none()

    async def list_processed(
        self, tenant_id: str, limit: int = 50, offset: int = 0
    ) -> list[tuple[DocumentEnrichment, Document]]:
        """Enrichments joined with their documents, newest first (Parsing Explorer)."""
        stmt = (
            select(DocumentEnrichment, Document)
            .join(Document, Document.id == DocumentEnrichment.document_id)
            .where(DocumentEnrichment.tenant_id == tenant_id)
            .order_by(DocumentEnrichment.updated_at.desc())
            .limit(limit)
            .offset(offset)
        )
        rows = (await self._session.execute(stmt)).all()
        return [(enrichment, document) for enrichment, document in rows]

    async def count_processed(self, tenant_id: str) -> int:
        stmt = select(func.count()).where(
            DocumentEnrichment.tenant_id == tenant_id,
            DocumentEnrichment.status == ProcessingStatus.PROCESSED,
        )
        return int((await self._session.execute(stmt)).scalar_one())

    async def category_distribution(
        self, tenant_id: str
    ) -> dict[DocumentCategory, int]:
        stmt = (
            select(DocumentEnrichment.category, func.count())
            .where(
                DocumentEnrichment.tenant_id == tenant_id,
                DocumentEnrichment.status == ProcessingStatus.PROCESSED,
            )
            .group_by(DocumentEnrichment.category)
        )
        rows = (await self._session.execute(stmt)).all()
        return {DocumentCategory(category): count for category, count in rows}
