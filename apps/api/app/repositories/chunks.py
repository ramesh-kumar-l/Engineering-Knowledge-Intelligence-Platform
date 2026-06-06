"""Chunk data access + statistics (tenant-scoped).

Chunks for a document are replaced wholesale on reprocessing so the store always
reflects the latest parse of each document.
"""

from __future__ import annotations

import uuid

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chunk import Chunk


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

    async def total_count(self, tenant_id: str) -> int:
        stmt = select(func.count()).where(Chunk.tenant_id == tenant_id)
        return int((await self._session.execute(stmt)).scalar_one())

    async def total_chars(self, tenant_id: str) -> int:
        stmt = select(func.coalesce(func.sum(Chunk.char_count), 0)).where(
            Chunk.tenant_id == tenant_id
        )
        return int((await self._session.execute(stmt)).scalar_one())
