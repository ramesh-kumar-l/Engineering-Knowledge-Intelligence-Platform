"""Sync run + event data access (tenant-scoped)."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.sync import SyncEvent, SyncRun


class SyncRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add_run(self, run: SyncRun) -> SyncRun:
        self._session.add(run)
        await self._session.flush()
        return run

    async def get_run(self, tenant_id: str, run_id: uuid.UUID) -> SyncRun | None:
        stmt = select(SyncRun).where(
            SyncRun.id == run_id, SyncRun.tenant_id == tenant_id
        )
        return (await self._session.execute(stmt)).scalar_one_or_none()

    async def list_runs(
        self,
        tenant_id: str,
        connector_id: uuid.UUID | None = None,
        limit: int = 50,
    ) -> list[SyncRun]:
        stmt = select(SyncRun).where(SyncRun.tenant_id == tenant_id)
        if connector_id is not None:
            stmt = stmt.where(SyncRun.connector_id == connector_id)
        stmt = stmt.order_by(SyncRun.started_at.desc()).limit(limit)
        return list((await self._session.execute(stmt)).scalars().all())

    def add_event(self, event: SyncEvent) -> None:
        self._session.add(event)

    async def list_events(self, tenant_id: str, run_id: uuid.UUID) -> list[SyncEvent]:
        stmt = (
            select(SyncEvent)
            .where(SyncEvent.tenant_id == tenant_id, SyncEvent.sync_run_id == run_id)
            .order_by(SyncEvent.created_at.asc())
        )
        return list((await self._session.execute(stmt)).scalars().all())
