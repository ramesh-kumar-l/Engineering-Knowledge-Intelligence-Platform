"""Agent engine — dispatches, runs and persists an agent execution (Phase 8, ADR-0021).

Builds the shared ``AgentContext`` over retrieval + trust + graph + intelligence, runs
the selected deterministic planner, and persists the run: each plan step becomes an
``AgentStep`` row (the trace for the Execution Viewer) and the conclusions are stored as
a JSON snapshot on the ``AgentRun`` (the Audit Trail record). Planner failures are
captured as a failed step + a failed run, never raised (same posture as ADR-0009).
"""

from __future__ import annotations

import uuid
from collections.abc import Awaitable, Callable

from app.agents import (
    architecture_agent,
    incident_agent,
    maintenance_agent,
    onboarding_agent,
    serialize,
)
from app.agents.base import AgentReport
from app.agents.catalog import info_for
from app.agents.context import AgentContext
from app.domain.enums import AgentStepStatus, AgentType, SyncStatus
from app.graph.store import GraphStore
from app.intelligence.intelligence_service import IntelligenceService
from app.models.agent import AgentRun, AgentStep
from app.repositories.agents import AgentRepository
from app.retrieval.search_service import SearchService
from app.trust.trust_service import TrustService

_TITLE_CHARS = 160

_PLANNERS: dict[AgentType, Callable[[AgentContext, str], Awaitable[AgentReport]]] = {
    AgentType.INCIDENT: incident_agent.run,
    AgentType.ONBOARDING: onboarding_agent.run,
    AgentType.ARCHITECTURE: architecture_agent.run,
    AgentType.MAINTENANCE: maintenance_agent.run,
}


class AgentService:
    def __init__(
        self,
        agents_repo: AgentRepository,
        search: SearchService,
        trust: TrustService,
        graph: GraphStore,
        intelligence: IntelligenceService,
    ) -> None:
        self._repo = agents_repo
        self._search = search
        self._trust = trust
        self._graph = graph
        self._intelligence = intelligence

    async def run(
        self, tenant_id: str, actor: str, agent_type: AgentType, target: str | None
    ) -> AgentRun:
        """Run an agent and persist the run + steps; returns the finished run."""
        target = (target or "").strip()
        run = await self._repo.create_run(
            AgentRun(
                tenant_id=tenant_id,
                agent_type=agent_type,
                target=target or None,
                title=_title(agent_type, target),
                status=SyncStatus.RUNNING,
                created_by=actor,
            )
        )
        ctx = AgentContext(
            tenant_id=tenant_id,
            search=self._search,
            trust=self._trust,
            graph=self._graph,
            intelligence=self._intelligence,
        )
        try:
            report = await _PLANNERS[agent_type](ctx, target)
            for ordinal, step in enumerate(report.steps):
                await self._repo.add_step(
                    AgentStep(
                        run_id=run.id,
                        tenant_id=tenant_id,
                        ordinal=ordinal,
                        name=step.name,
                        status=step.status,
                        summary=step.summary,
                        detail_json=step.detail or None,
                    )
                )
            run.status = SyncStatus.SUCCEEDED
            run.confidence = report.confidence
            run.result_json = serialize.result_to_dict(report)
        except Exception as exc:  # planner failure is captured, not raised (ADR-0009)
            await self._repo.add_step(
                AgentStep(
                    run_id=run.id,
                    tenant_id=tenant_id,
                    ordinal=0,
                    name="Run agent",
                    status=AgentStepStatus.FAILED,
                    summary=f"Agent failed: {exc}",
                    detail_json=None,
                )
            )
            run.status = SyncStatus.FAILED
        await self._repo.finish_run(run)
        return run

    async def list_runs(
        self, tenant_id: str, limit: int = 50, offset: int = 0
    ) -> list[tuple[AgentRun, int]]:
        return await self._repo.list_recent(tenant_id, limit, offset)

    async def get_run(
        self, tenant_id: str, run_id: uuid.UUID
    ) -> tuple[AgentRun, list[AgentStep]] | None:
        run = await self._repo.get(tenant_id, run_id)
        if run is None:
            return None
        steps = await self._repo.list_steps(tenant_id, run_id)
        return run, steps


def _title(agent_type: AgentType, target: str) -> str:
    label = info_for(agent_type).label
    text = f"{label}: {target}" if target else label
    return text[:_TITLE_CHARS] + ("…" if len(text) > _TITLE_CHARS else "")
