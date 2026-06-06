"""Graph engine tests — projection build + curation against SQLite + in-memory store."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.enums import EntityKind, RelationshipType, SourceType, SyncStatus
from app.graph.store import InMemoryGraphStore
from app.models.connector import Connector
from app.models.document import Document
from app.repositories.connectors import ConnectorRepository
from app.repositories.documents import DocumentRepository
from app.repositories.graph_build import GraphBuildRepository
from app.services.graph_service import GraphService


def _service(session: AsyncSession, store: InMemoryGraphStore) -> GraphService:
    return GraphService(
        GraphBuildRepository(session),
        ConnectorRepository(session),
        DocumentRepository(session),
        store,
    )


async def _seed_document(session: AsyncSession) -> Document:
    connector = Connector(
        tenant_id="acme",
        source_type=SourceType.GITHUB,
        name="repo",
        config={"owner": "octo", "repo": "app"},
    )
    session.add(connector)
    await session.flush()
    doc = Document(
        tenant_id="acme",
        connector_id=connector.id,
        source_type=SourceType.GITHUB,
        external_id="1",
        title="Fix login",
        content_hash="h",
        raw_content="body",
        doc_metadata={"author": "alice"},
    )
    session.add(doc)
    await session.flush()
    return doc


async def test_build_projects_entities_and_relationships(db_session: AsyncSession) -> None:
    await _seed_document(db_session)
    store = InMemoryGraphStore()

    run = await _service(db_session, store).build("acme")
    assert run.status == SyncStatus.SUCCEEDED
    assert run.documents_seen == 1
    assert run.entity_count >= 3  # repository + team + engineer + document

    stats = await store.stats("acme")
    assert stats.entities_by_kind.get("repository") == 1
    assert stats.entities_by_kind.get("engineer") == 1
    assert stats.relationships_by_type.get("modified", 0) >= 1


async def test_build_is_idempotent(db_session: AsyncSession) -> None:
    await _seed_document(db_session)
    store = InMemoryGraphStore()
    service = _service(db_session, store)

    first = await service.build("acme")
    second = await service.build("acme")
    assert second.entity_count == first.entity_count
    assert (await store.stats("acme")).total_entities == first.entity_count


async def test_create_relationship_curates_services_and_dependency(
    db_session: AsyncSession,
) -> None:
    store = InMemoryGraphStore()
    service = _service(db_session, store)

    rel = await service.create_relationship(
        "acme",
        RelationshipType.DEPENDS_ON,
        EntityKind.SERVICE,
        "Checkout",
        EntityKind.SERVICE,
        "Payments",
    )
    assert rel.from_key == "service:checkout"
    assert rel.to_key == "service:payments"

    services = await store.list_entities("acme", EntityKind.SERVICE)
    assert {s.name for s in services} == {"Checkout", "Payments"}
    deps = await store.list_relationships("acme", RelationshipType.DEPENDS_ON)
    assert len(deps) == 1
