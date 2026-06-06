"""Intelligence service over SQLite + in-memory graph (Phase 7)."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.enums import (
    EntityKind,
    ProcessingStatus,
    RelationshipType,
    SourceType,
)
from app.graph.base import GraphEntity, GraphRelationship, entity_key
from app.graph.store import InMemoryGraphStore
from app.intelligence.intelligence_service import IntelligenceService
from app.models.connector import Connector
from app.models.document import Document
from app.models.embedding import DocumentEmbeddingState
from app.models.enrichment import DocumentEnrichment
from app.repositories.chunks import ChunkRepository
from app.repositories.trust import TrustRepository
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

    # Healthy doc: processed, embedded, owned, fresh -> not debt.
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
    # Debt doc: unprocessed, unembedded, unowned, stale.
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
    session.add(
        DocumentEmbeddingState(
            tenant_id="acme",
            document_id=good.id,
            source_content_hash="hg",
            chunk_count=5,
            model="hashing-256",
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


def _service(session: AsyncSession, graph: InMemoryGraphStore) -> IntelligenceService:
    trust = TrustService(TrustRepository(session), ChunkRepository(session), graph)
    return IntelligenceService(graph, trust)


async def test_dependencies_detect_cycle(db_session: AsyncSession) -> None:
    graph = InMemoryGraphStore()
    await _seed(db_session, graph)
    report = await _service(db_session, graph).dependencies("acme")
    assert report.total_dependencies == 2
    assert report.cycle_count == 1
    assert {n.key for n in report.nodes} == {"service:checkout", "service:ledger"}


async def test_debt_flags_unowned_stale_doc(db_session: AsyncSession) -> None:
    graph = InMemoryGraphStore()
    debt_id = await _seed(db_session, graph)
    report = await _service(db_session, graph).debt("acme")
    assert report.total_documents == 2
    debt_ids = {i.document_id for i in report.items}
    assert debt_id in debt_ids
    item = next(i for i in report.items if i.document_id == debt_id)
    assert "unowned" in item.reasons and "stale" in item.reasons


async def test_incidents_report(db_session: AsyncSession) -> None:
    graph = InMemoryGraphStore()
    await _seed(db_session, graph)
    report = await _service(db_session, graph).incidents("acme")
    assert report.total_incidents == 1
    assert report.unresolved_count == 1  # no resolved edge seeded
    assert report.impacted_components[0].key == "repository:octo/app"


async def test_ownership_coverage(db_session: AsyncSession) -> None:
    graph = InMemoryGraphStore()
    await _seed(db_session, graph)
    report = await _service(db_session, graph).ownership("acme")
    # repository owned (team) + good doc owned (engineer); debt doc and services orphaned.
    assert report.overall_owned >= 2
    orphan_keys = {o.key for o in report.orphans}
    assert "service:checkout" in orphan_keys


async def test_overview_aggregates(db_session: AsyncSession) -> None:
    graph = InMemoryGraphStore()
    await _seed(db_session, graph)
    overview = await _service(db_session, graph).overview("acme")
    assert overview.dependency_cycles == 1
    assert overview.debt_count >= 1
    assert overview.incidents_total == 1
    assert 0.0 <= overview.ownership_coverage <= 1.0


async def test_tenant_isolation(db_session: AsyncSession) -> None:
    graph = InMemoryGraphStore()
    await _seed(db_session, graph)
    service = _service(db_session, graph)
    assert (await service.dependencies("other")).total_dependencies == 0
    assert (await service.debt("other")).total_documents == 0
    assert (await service.incidents("other")).total_incidents == 0
