"""Embedding run/event + per-document state data access (tenant-scoped).

Runs/events mirror ``GraphBuildRepository``; the state table is the staleness ledger
that lets a re-run skip documents whose content has not changed since last embedded.
"""

from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.embedding import (
    DocumentEmbeddingState,
    EmbeddingEvent,
    EmbeddingRun,
)


class EmbeddingRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add_run(self, run: EmbeddingRun) -> EmbeddingRun:
        self._session.add(run)
        await self._session.flush()
        return run

    async def get_run(self, tenant_id: str, run_id: uuid.UUID) -> EmbeddingRun | None:
        stmt = select(EmbeddingRun).where(
            EmbeddingRun.id == run_id, EmbeddingRun.tenant_id == tenant_id
        )
        return (await self._session.execute(stmt)).scalar_one_or_none()

    async def list_runs(self, tenant_id: str, limit: int = 50) -> list[EmbeddingRun]:
        stmt = (
            select(EmbeddingRun)
            .where(EmbeddingRun.tenant_id == tenant_id)
            .order_by(EmbeddingRun.started_at.desc())
            .limit(limit)
        )
        return list((await self._session.execute(stmt)).scalars().all())

    def add_event(self, event: EmbeddingEvent) -> None:
        self._session.add(event)

    async def list_events(
        self, tenant_id: str, run_id: uuid.UUID
    ) -> list[EmbeddingEvent]:
        stmt = (
            select(EmbeddingEvent)
            .where(
                EmbeddingEvent.tenant_id == tenant_id,
                EmbeddingEvent.embedding_run_id == run_id,
            )
            .order_by(EmbeddingEvent.created_at.asc())
        )
        return list((await self._session.execute(stmt)).scalars().all())

    async def get_state(
        self, tenant_id: str, document_id: uuid.UUID
    ) -> DocumentEmbeddingState | None:
        stmt = select(DocumentEmbeddingState).where(
            DocumentEmbeddingState.tenant_id == tenant_id,
            DocumentEmbeddingState.document_id == document_id,
        )
        return (await self._session.execute(stmt)).scalar_one_or_none()

    async def add_state(self, state: DocumentEmbeddingState) -> DocumentEmbeddingState:
        self._session.add(state)
        await self._session.flush()
        return state

    async def count_embedded_documents(self, tenant_id: str) -> int:
        stmt = select(func.count()).where(
            DocumentEmbeddingState.tenant_id == tenant_id
        )
        return int((await self._session.execute(stmt)).scalar_one())
