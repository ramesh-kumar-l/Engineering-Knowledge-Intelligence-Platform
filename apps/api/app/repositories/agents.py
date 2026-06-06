"""Agent run + step persistence (tenant-scoped) — Phase 8.

Backs the Agent Workspace (recent runs), Execution Viewer (run + ordered steps) and
Audit Trail (all runs). Every query is filtered by ``tenant_id`` so runs never leak
across tenants.
"""

from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent import AgentRun, AgentStep


class AgentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_run(self, run: AgentRun) -> AgentRun:
        self._session.add(run)
        await self._session.flush()
        return run

    async def add_step(self, step: AgentStep) -> AgentStep:
        self._session.add(step)
        await self._session.flush()
        return step

    async def finish_run(self, run: AgentRun) -> AgentRun:
        """Persist the run's terminal status/result after its steps are written."""
        await self._session.flush()
        return run

    async def get(self, tenant_id: str, run_id: uuid.UUID) -> AgentRun | None:
        stmt = select(AgentRun).where(
            AgentRun.id == run_id, AgentRun.tenant_id == tenant_id
        )
        return (await self._session.execute(stmt)).scalar_one_or_none()

    async def list_recent(
        self, tenant_id: str, limit: int = 50, offset: int = 0
    ) -> list[tuple[AgentRun, int]]:
        """Runs (most recent first) with their step counts."""
        step_count = func.count(AgentStep.id)
        stmt = (
            select(AgentRun, step_count)
            .outerjoin(AgentStep, AgentStep.run_id == AgentRun.id)
            .where(AgentRun.tenant_id == tenant_id)
            .group_by(AgentRun.id)
            .order_by(AgentRun.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        rows = (await self._session.execute(stmt)).all()
        return [(row[0], int(row[1])) for row in rows]

    async def list_steps(
        self, tenant_id: str, run_id: uuid.UUID
    ) -> list[AgentStep]:
        stmt = (
            select(AgentStep)
            .where(AgentStep.tenant_id == tenant_id, AgentStep.run_id == run_id)
            .order_by(AgentStep.ordinal.asc())
        )
        return list((await self._session.execute(stmt)).scalars().all())
