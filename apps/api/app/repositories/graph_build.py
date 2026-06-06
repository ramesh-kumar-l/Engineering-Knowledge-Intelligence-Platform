"""Graph-build run + event data access (tenant-scoped). Mirrors ProcessingRepository."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.graph import GraphBuildEvent, GraphBuildRun


class GraphBuildRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add_run(self, run: GraphBuildRun) -> GraphBuildRun:
        self._session.add(run)
        await self._session.flush()
        return run

    async def get_run(self, tenant_id: str, run_id: uuid.UUID) -> GraphBuildRun | None:
        stmt = select(GraphBuildRun).where(
            GraphBuildRun.id == run_id, GraphBuildRun.tenant_id == tenant_id
        )
        return (await self._session.execute(stmt)).scalar_one_or_none()

    async def list_runs(self, tenant_id: str, limit: int = 50) -> list[GraphBuildRun]:
        stmt = (
            select(GraphBuildRun)
            .where(GraphBuildRun.tenant_id == tenant_id)
            .order_by(GraphBuildRun.started_at.desc())
            .limit(limit)
        )
        return list((await self._session.execute(stmt)).scalars().all())

    def add_event(self, event: GraphBuildEvent) -> None:
        self._session.add(event)

    async def list_events(
        self, tenant_id: str, run_id: uuid.UUID
    ) -> list[GraphBuildEvent]:
        stmt = (
            select(GraphBuildEvent)
            .where(
                GraphBuildEvent.tenant_id == tenant_id,
                GraphBuildEvent.graph_build_run_id == run_id,
            )
            .order_by(GraphBuildEvent.created_at.asc())
        )
        return list((await self._session.execute(stmt)).scalars().all())
