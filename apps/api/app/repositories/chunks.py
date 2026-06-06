"""Chunk data access + statistics (tenant-scoped).

Chunks for a document are replaced wholesale on reprocessing so the store always
reflects the latest parse of each document.
"""

from __future__ import annotations

import uuid

from sqlalchemy import delete, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chunk import Chunk
from app.models.document import Document


class ChunkRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def replace_for_document(
        self, tenant_id: str, document_id: uuid.UUID, chunks: list[Chunk]
    ) -> None:
        await self._session.execute(
            delete(Chunk).where(
                Chunk.tenant_id == tenant_id, Chunk.document_id == document_id
            )
        )
        for chunk in chunks:
            self._session.add(chunk)
        await self._session.flush()

    async def list_by_document(
        self, tenant_id: str, document_id: uuid.UUID
    ) -> list[Chunk]:
        stmt = (
            select(Chunk)
            .where(Chunk.tenant_id == tenant_id, Chunk.document_id == document_id)
            .order_by(Chunk.ordinal.asc())
        )
        return list((await self._session.execute(stmt)).scalars().all())

    async def list_documents_with_chunks(self, tenant_id: str) -> list[Document]:
        """Non-deleted documents that have at least one chunk (embedding input)."""
        stmt = (
            select(Document)
            .join(Chunk, Chunk.document_id == Document.id)
            .where(Document.tenant_id == tenant_id, Document.is_deleted.is_(False))
            .group_by(Document.id)
            .order_by(Document.updated_at.asc())
        )
        return list((await self._session.execute(stmt)).scalars().all())

    async def search_candidates(
        self, tenant_id: str, terms: list[str], limit: int = 50
    ) -> list[tuple[Chunk, Document]]:
        """Chunks (with their document) matching any query term via a portable LIKE.

        Candidate retrieval only — final ranking is done deterministically in Python
        (``retrieval.keyword``). ``ilike`` compiles to ``ILIKE`` on PostgreSQL and a
        case-insensitive ``LIKE`` on SQLite, keeping prod/test parity.
        """
        if not terms:
            return []
        conditions = [Chunk.content.ilike(f"%{term}%") for term in terms]
        stmt = (
            select(Chunk, Document)
            .join(Document, Document.id == Chunk.document_id)
            .where(
                Chunk.tenant_id == tenant_id,
                Document.is_deleted.is_(False),
                or_(*conditions),
            )
            .limit(limit)
        )
        rows = (await self._session.execute(stmt)).all()
        return [(chunk, document) for chunk, document in rows]

    async def total_count(self, tenant_id: str) -> int:
        stmt = select(func.count()).where(Chunk.tenant_id == tenant_id)
        return int((await self._session.execute(stmt)).scalar_one())

    async def total_chars(self, tenant_id: str) -> int:
        stmt = select(func.coalesce(func.sum(Chunk.char_count), 0)).where(
            Chunk.tenant_id == tenant_id
        )
        return int((await self._session.execute(stmt)).scalar_one())
