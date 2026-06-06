"""Document data access — tenant-scoped, keyed by source identity for change tracking."""

from __future__ import annotations

import uuid
from collections.abc import Sequence

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.enums import ProcessingStatus
from app.models.document import Document
from app.models.enrichment import DocumentEnrichment


class DocumentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, document: Document) -> Document:
        self._session.add(document)
        await self._session.flush()
        return document

    async def get(self, tenant_id: str, document_id: uuid.UUID) -> Document | None:
        stmt = select(Document).where(
            Document.id == document_id, Document.tenant_id == tenant_id
        )
        return (await self._session.execute(stmt)).scalar_one_or_none()

    async def get_by_external_id(
        self, tenant_id: str, connector_id: uuid.UUID, external_id: str
    ) -> Document | None:
        stmt = select(Document).where(
            Document.tenant_id == tenant_id,
            Document.connector_id == connector_id,
            Document.external_id == external_id,
        )
        return (await self._session.execute(stmt)).scalar_one_or_none()

    async def list(
        self,
        tenant_id: str,
        connector_id: uuid.UUID | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Document]:
        stmt = select(Document).where(Document.tenant_id == tenant_id)
        if connector_id is not None:
            stmt = stmt.where(Document.connector_id == connector_id)
        stmt = stmt.order_by(Document.updated_at.desc()).limit(limit).offset(offset)
        return list((await self._session.execute(stmt)).scalars().all())

    async def list_with_enrichment(
        self, tenant_id: str, limit: int = 1000
    ) -> Sequence[tuple[Document, DocumentEnrichment | None]]:
        """All non-deleted documents with their enrichment (Phase 3 graph projection).

        A left join so documents that have not been processed yet still project as
        Document nodes (without a category), keeping the graph aligned with ingestion.
        """
        stmt = (
            select(Document, DocumentEnrichment)
            .outerjoin(
                DocumentEnrichment, DocumentEnrichment.document_id == Document.id
            )
            .where(Document.tenant_id == tenant_id, Document.is_deleted.is_(False))
            .order_by(Document.updated_at.asc())
            .limit(limit)
        )
        rows = (await self._session.execute(stmt)).all()
        return [(document, enrichment) for document, enrichment in rows]

    async def list_pending_processing(
        self,
        tenant_id: str,
        connector_id: uuid.UUID | None = None,
        limit: int = 100,
    ) -> Sequence[Document]:
        """Documents that need (re)processing: never processed, stale, or failed.

        A left join to the enrichment lets one query find new documents, documents
        whose source content changed since they were last processed, and documents
        whose previous processing failed.
        """
        stmt = (
            select(Document)
            .outerjoin(
                DocumentEnrichment,
                DocumentEnrichment.document_id == Document.id,
            )
            .where(
                Document.tenant_id == tenant_id,
                Document.is_deleted.is_(False),
                or_(
                    DocumentEnrichment.id.is_(None),
                    DocumentEnrichment.source_content_hash != Document.content_hash,
                    DocumentEnrichment.status == ProcessingStatus.FAILED,
                ),
            )
        )
        if connector_id is not None:
            stmt = stmt.where(Document.connector_id == connector_id)
        stmt = stmt.order_by(Document.updated_at.asc()).limit(limit)
        return list((await self._session.execute(stmt)).scalars().all())
