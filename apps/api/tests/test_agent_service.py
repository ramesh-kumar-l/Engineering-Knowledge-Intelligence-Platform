"""Agent service: orchestration + persistence over SQLite + in-memory graph (Phase 8)."""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.agent_service import AgentService
from app.domain.enums import AgentType, SyncStatus
from app.graph.store import InMemoryGraphStore
from app.intelligence.intelligence_service import IntelligenceService
from app.repositories.agents import AgentRepository
from app.repositories.chunks import ChunkRepository
from app.repositories.trust import TrustRepository
from app.retrieval.embedder import HashingEmbedder
from app.retrieval.search_service import SearchService
from app.retrieval.vector_store import InMemoryVectorStore
from app.trust.trust_service import TrustService
from tests.test_agents_planners import _seed


def _service(session: AsyncSession, graph: InMemoryGraphStore) -> AgentService:
    chunk = ChunkRepository(session)
    search = SearchService(HashingEmbedder(), InMemoryVectorStore(), chunk, graph)
    trust = TrustService(TrustRepository(session), chunk, graph)
    intelligence = IntelligenceService(graph, trust)
    return AgentService(AgentRepository(session), search, trust, graph, intelligence)


async def test_run_persists_run_and_steps(db_session: AsyncSession) -> None:
    graph = InMemoryGraphStore()
    await _seed(db_session, graph)
    service = _service(db_session, graph)

    run = await service.run("acme", "dev", AgentType.MAINTENANCE, None)
    assert run.status == SyncStatus.SUCCEEDED
    assert run.result_json is not None
    assert run.confidence is not None

    fetched = await service.get_run("acme", run.id)
    assert fetched is not None
    fetched_run, steps = fetched
    assert fetched_run.id == run.id
    assert len(steps) >= 1
    assert [s.ordinal for s in steps] == sorted(s.ordinal for s in steps)


async def test_list_runs(db_session: AsyncSession) -> None:
    graph = InMemoryGraphStore()
    await _seed(db_session, graph)
    service = _service(db_session, graph)
    await service.run("acme", "dev", AgentType.INCIDENT, "outage")
    await service.run("acme", "dev", AgentType.MAINTENANCE, None)
    rows = await service.list_runs("acme")
    assert len(rows) == 2
    # Most recent first; each row carries its step count.
    assert all(count >= 1 for _, count in rows)


async def test_tenant_isolation(db_session: AsyncSession) -> None:
    graph = InMemoryGraphStore()
    await _seed(db_session, graph)
    service = _service(db_session, graph)
    run = await service.run("acme", "dev", AgentType.MAINTENANCE, None)
    assert await service.get_run("other", run.id) is None
    assert await service.list_runs("other") == []


async def test_get_unknown_run(db_session: AsyncSession) -> None:
    graph = InMemoryGraphStore()
    service = _service(db_session, graph)
    assert await service.get_run("acme", uuid.uuid4()) is None
