"""Agent planners over SQLite + in-memory graph/vector stores (Phase 8).

Evidence gathering (hybrid search) is exercised against an empty index, so these tests
focus on the graph/intelligence-derived conclusions each planner draws; the search
steps correctly report a surfaced gap (EMPTY) rather than failing.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.agents import (
    architecture_agent,
    incident_agent,
    maintenance_agent,
    onboarding_agent,
)
from app.agents.context import AgentContext
from app.domain.enums import (
    AgentStepStatus,
    AgentType,
    EntityKind,
    ProcessingStatus,
    RelationshipType,
    RiskBand,
    SourceType,
)
from app.graph.base import GraphEntity, GraphRelationship, entity_key
from app.graph.store import InMemoryGraphStore
from app.intelligence.intelligence_service import IntelligenceService
from app.models.connector import Connector
from app.models.document import Document
from app.models.enrichment import DocumentEnrichment
from app.repositories.chunks import ChunkRepository
from app.repositories.trust import TrustRepository
from app.retrieval.embedder import HashingEmbedder
from app.retrieval.search_service import SearchService
from app.retrieval.vector_store import InMemoryVectorStore
from app.trust.trust_service import TrustService


async def _seed(session: AsyncSession, graph: InMemoryGraphStore) -> uuid.UUID:
    now = datetime.now(UTC)
    connector = Connector(
        tenant_id="acme",
        source_type=SourceType.GITHUB,
        name="repo",
        config={"owner": "octo", "repo": "app"},
    )
    session.add(connector)
    await session.flush()

    good = Document(
        tenant_id="acme",
        connector_id=connector.id,
        source_type=SourceType.GITHUB,
        external_id="good",
        title="Checkout architecture",
        content_hash="hg",
        raw_content="x",
        source_updated_at=now,
    )
    debt = Document(
        tenant_id="acme",
        connector_id=connector.id,
        source_type=SourceType.GITHUB,
        external_id="debt",
        title="Forgotten runbook",
        content_hash="hd",
        raw_content="y",
        source_updated_at=now - timedelta(days=600),
    )
    session.add_all([good, debt])
    await session.flush()
    session.add(
        DocumentEnrichment(
            tenant_id="acme",
            document_id=good.id,
            source_content_hash="hg",
            status=ProcessingStatus.PROCESSED,
            chunk_count=5,
            word_count=500,
        )
    )

    good_key = entity_key(EntityKind.DOCUMENT, str(good.id))
    eng = entity_key(EntityKind.ENGINEER, "octocat")
    team = entity_key(EntityKind.TEAM, "octo")
    checkout = entity_key(EntityKind.SERVICE, "checkout")
    ledger = entity_key(EntityKind.SERVICE, "ledger")
    repo = entity_key(EntityKind.REPOSITORY, "octo/app")
    inc = entity_key(EntityKind.INCIDENT, "outage")

    def _ent(kind: EntityKind, key: str, name: str) -> GraphEntity:
        return GraphEntity(tenant_id="acme", kind=kind, key=key, name=name)

    def _rel(rtype: RelationshipType, src: str, dst: str) -> GraphRelationship:
        return GraphRelationship(tenant_id="acme", type=rtype, from_key=src, to_key=dst)

    for ent in (
        _ent(EntityKind.ENGINEER, eng, "octocat"),
        _ent(EntityKind.DOCUMENT, good_key, good.title),
        _ent(EntityKind.SERVICE, checkout, "checkout"),
        _ent(EntityKind.SERVICE, ledger, "ledger"),
        _ent(EntityKind.REPOSITORY, repo, "octo/app"),
        _ent(EntityKind.INCIDENT, inc, "Outage"),
    ):
        await graph.upsert_entity(ent)
    for rel in (
        _rel(RelationshipType.MODIFIED, eng, good_key),
        _rel(RelationshipType.OWNS, team, repo),
        _rel(RelationshipType.DEPENDS_ON, checkout, ledger),
        _rel(RelationshipType.DEPENDS_ON, ledger, checkout),
        _rel(RelationshipType.IMPACTS, inc, repo),
    ):
        await graph.upsert_relationship(rel)
    await session.flush()
    return debt.id


def _ctx(session: AsyncSession, graph: InMemoryGraphStore) -> AgentContext:
    chunk = ChunkRepository(session)
    search = SearchService(HashingEmbedder(), InMemoryVectorStore(), chunk, graph)
    trust = TrustService(TrustRepository(session), chunk, graph)
    return AgentContext("acme", search, trust, graph, IntelligenceService(graph, trust))


async def test_incident_agent_flags_unresolved(db_session: AsyncSession) -> None:
    graph = InMemoryGraphStore()
    await _seed(db_session, graph)
    report = await incident_agent.run(_ctx(db_session, graph), "outage")
    assert report.agent_type == AgentType.INCIDENT
    assert any(f.label.startswith("Incident:") for f in report.findings)
    assert any(a.priority == RiskBand.HIGH for a in report.actions)
    assert len(report.steps) == 3


async def test_onboarding_agent_maps_dependencies(db_session: AsyncSession) -> None:
    graph = InMemoryGraphStore()
    await _seed(db_session, graph)
    report = await onboarding_agent.run(_ctx(db_session, graph), "checkout")
    assert report.agent_type == AgentType.ONBOARDING
    dep = next(f for f in report.findings if f.label == "Dependency profile")
    # checkout sits in the checkout<->ledger cycle.
    assert dep.severity == RiskBand.MEDIUM
    # An owner is discoverable via the modified "Checkout architecture" doc.
    assert any(f.label == "Owners to contact" for f in report.findings)


async def test_onboarding_agent_requires_target(db_session: AsyncSession) -> None:
    graph = InMemoryGraphStore()
    await _seed(db_session, graph)
    report = await onboarding_agent.run(_ctx(db_session, graph), "")
    assert report.target is None
    assert report.steps[0].status == AgentStepStatus.EMPTY


async def test_architecture_agent_detects_cycle(db_session: AsyncSession) -> None:
    graph = InMemoryGraphStore()
    await _seed(db_session, graph)
    report = await architecture_agent.run(_ctx(db_session, graph), "checkout")
    cycle_findings = [f for f in report.findings if f.label == "Circular dependency"]
    assert cycle_findings and cycle_findings[0].severity == RiskBand.HIGH
    assert any(a.action.startswith("Break the circular") for a in report.actions)


async def test_maintenance_agent_surfaces_debt(db_session: AsyncSession) -> None:
    graph = InMemoryGraphStore()
    debt_id = await _seed(db_session, graph)
    report = await maintenance_agent.run(_ctx(db_session, graph), "")
    assert report.agent_type == AgentType.MAINTENANCE
    assert any(e.document_id == debt_id for e in report.evidence)
    orphan_refs = {r for f in report.findings if f.label == "Orphaned components" for r in f.refs}
    assert "service:checkout" in orphan_refs
