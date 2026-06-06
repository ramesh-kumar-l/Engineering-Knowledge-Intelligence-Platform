"""Processing run + event data access (tenant-scoped). Mirrors SyncRepository."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.processing import ProcessingEvent, ProcessingRun


class ProcessingRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add_run(self, run: ProcessingRun) -> ProcessingRun:
        self._session.add(run)
        await self._session.flush()
        return run

    async def get_run(self, tenant_id: str, run_id: uuid.UUID) -> ProcessingRun | None:
        stmt = select(ProcessingRun).where(
            ProcessingRun.id == run_id, ProcessingRun.tenant_id == tenant_id
        )
        return (await self._session.execute(stmt)).scalar_one_or_none()

    async def list_runs(
        self, tenant_id: str, limit: int = 50
    ) -> list[ProcessingRun]:
        stmt = (
            select(ProcessingRun)
            .where(ProcessingRun.tenant_id == tenant_id)
            .order_by(ProcessingRun.started_at.desc())
            .limit(limit)
        )
        return list((await self._session.execute(stmt)).scalars().all())

    def add_event(self, event: ProcessingEvent) -> None:
        self._session.add(event)

    async def list_events(
        self, tenant_id: str, run_id: uuid.UUID
    ) -> list[ProcessingEvent]:
        stmt = (
            select(ProcessingEvent)
            .where(
                ProcessingEvent.tenant_id == tenant_id,
                ProcessingEvent.processing_run_id == run_id,
            )
            .order_by(ProcessingEvent.created_at.asc())
        )
        return list((await self._session.execute(stmt)).scalars().all())
