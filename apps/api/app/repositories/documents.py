"""Document data access — tenant-scoped, keyed by source identity for change tracking."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document


class DocumentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, document: Document) -> Document:
        self._session.add(document)
        await self._session.flush()
        return document

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
