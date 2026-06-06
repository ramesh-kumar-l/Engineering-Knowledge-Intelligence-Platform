"""Trust service tests — profile/sources/freshness (SQLite + in-memory graph)."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.enums import (
    ConfidenceBand,
    EntityKind,
    FreshnessBand,
    GraphSource,
    ProcessingStatus,
    RelationshipType,
    SourceType,
)
from app.graph.base import GraphEntity, GraphRelationship, entity_key
from app.graph.store import InMemoryGraphStore
from app.models.chunk import Chunk
from app.models.connector import Connector
from app.models.document import Document
from app.models.embedding import DocumentEmbeddingState
from app.models.enrichment import DocumentEnrichment
from app.repositories.chunks import ChunkRepository
from app.repositories.trust import TrustRepository
from app.trust.trust_service import TrustService


async def _seed(session: AsyncSession, graph: InMemoryGraphStore) -> dict[str, uuid.UUID]:
    now = datetime.now(UTC)
    connector = Connector(
        tenant_id="acme",
        source_type=SourceType.GITHUB,
        name="repo",
        config={"owner": "octo", "repo": "app"},
    )
    session.add(connector)
    await session.flush()

    # Doc A — fresh, processed, embedded, owned => high confidence.
    doc_a = Document(
        tenant_id="acme",
        connector_id=connector.id,
        source_type=SourceType.GITHUB,
        external_id="a",
        title="Checkout architecture",
        content_hash="ha",
        raw_content="how checkout works",
        source_updated_at=now,
    )
    session.add(doc_a)
    await session.flush()
    session.add(
        Chunk(
            tenant_id="acme",
            document_id=doc_a.id,
            ordinal=0,
            content="how checkout works end to end",
            content_hash="ca",
        )
    )
    session.add(
        DocumentEnrichment(
            tenant_id="acme",
            document_id=doc_a.id,
            source_content_hash="ha",
            status=ProcessingStatus.PROCESSED,
            chunk_count=5,
            word_count=500,
        )
    )
    session.add(
        DocumentEmbeddingState(
            tenant_id="acme",
            document_id=doc_a.id,
            source_content_hash="ha",
            chunk_count=5,
            model="hashing-256",
        )
    )

    # Doc B — old, never processed/embedded, no owner => low confidence + stale.
    doc_b = Document(
        tenant_id="acme",
        connector_id=connector.id,
        source_type=SourceType.JIRA,
        external_id="b",
        title="Legacy migration notes",
        content_hash="hb",
        raw_content="old notes",
        source_updated_at=now - timedelta(days=400),
    )
    session.add(doc_b)
    await session.flush()

    # Ownership for A from the graph: an engineer modified the document.
    doc_a_key = entity_key(EntityKind.DOCUMENT, str(doc_a.id))
    eng_key = entity_key(EntityKind.ENGINEER, "octocat")
    await graph.upsert_entity(
        GraphEntity(
            tenant_id="acme",
            kind=EntityKind.ENGINEER,
            key=eng_key,
            name="octocat",
            source=GraphSource.PROJECTION,
        )
    )
    await graph.upsert_entity(
        GraphEntity(
            tenant_id="acme",
            kind=EntityKind.DOCUMENT,
            key=doc_a_key,
            name=doc_a.title,
            source=GraphSource.PROJECTION,
        )
    )
    await graph.upsert_relationship(
        GraphRelationship(
            tenant_id="acme",
            type=RelationshipType.MODIFIED,
            from_key=eng_key,
            to_key=doc_a_key,
        )
    )
    await session.flush()
    return {"a": doc_a.id, "b": doc_b.id}


def _service(session: AsyncSession, graph: InMemoryGraphStore) -> TrustService:
    return TrustService(TrustRepository(session), ChunkRepository(session), graph)


async def test_profile_high_confidence_owned_fresh(db_session: AsyncSession) -> None:
    graph = InMemoryGraphStore()
    ids = await _seed(db_session, graph)
    profile = await _service(db_session, graph).profile("acme", ids["a"])

    assert profile is not None
    assert profile.confidence_band == ConfidenceBand.HIGH
    assert profile.freshness_band == FreshnessBand.FRESH
    assert profile.ownership_known is True
    assert profile.owners[0].name == "octocat"
    assert profile.evidence  # excerpts attached
    assert round(sum(profile.signals.values()), 4) == profile.confidence


async def test_profile_low_confidence_stale_unowned(db_session: AsyncSession) -> None:
    graph = InMemoryGraphStore()
    ids = await _seed(db_session, graph)
    profile = await _service(db_session, graph).profile("acme", ids["b"])

    assert profile is not None
    assert profile.confidence_band == ConfidenceBand.LOW
    assert profile.freshness_band == FreshnessBand.STALE
    assert profile.ownership_known is False
    assert profile.owners == []


async def test_profile_missing_returns_none(db_session: AsyncSession) -> None:
    graph = InMemoryGraphStore()
    await _seed(db_session, graph)
    assert await _service(db_session, graph).profile("acme", uuid.uuid4()) is None


async def test_sources_lists_with_owner_flag_and_filter(db_session: AsyncSession) -> None:
    graph = InMemoryGraphStore()
    ids = await _seed(db_session, graph)
    service = _service(db_session, graph)

    all_sources = await service.sources("acme")
    by_id = {s.document_id: s for s in all_sources}
    assert by_id[ids["a"]].has_owner is True
    assert by_id[ids["b"]].has_owner is False

    jira_only = await service.sources("acme", source_type=SourceType.JIRA)
    assert [s.document_id for s in jira_only] == [ids["b"]]


async def test_freshness_summary_buckets_and_stale(db_session: AsyncSession) -> None:
    graph = InMemoryGraphStore()
    ids = await _seed(db_session, graph)
    summary = await _service(db_session, graph).freshness("acme")

    assert summary.total == 2
    assert sum(b.count for b in summary.buckets) == 2
    assert ids["b"] in {s.document_id for s in summary.stale}


async def test_tenant_isolation(db_session: AsyncSession) -> None:
    graph = InMemoryGraphStore()
    ids = await _seed(db_session, graph)
    service = _service(db_session, graph)
    assert await service.profile("other", ids["a"]) is None
    assert await service.sources("other") == []
