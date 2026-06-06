"""Assistant service — ask/persist/continue over SQLite + in-memory graph/vector."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.assistant.assistant_service import AssistantService
from app.domain.enums import (
    AssistantIntent,
    EntityKind,
    MessageRole,
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
from app.repositories.conversations import ConversationRepository
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

    doc = Document(
        tenant_id="acme",
        connector_id=connector.id,
        source_type=SourceType.GITHUB,
        external_id="a",
        title="Checkout architecture",
        content_hash="ha",
        raw_content="how checkout works",
        source_updated_at=now,
    )
    session.add(doc)
    await session.flush()
    session.add(
        Chunk(
            tenant_id="acme",
            document_id=doc.id,
            ordinal=0,
            content="how the checkout service works end to end with payment capture",
            content_hash="ca",
        )
    )
    session.add(
        DocumentEnrichment(
            tenant_id="acme",
            document_id=doc.id,
            source_content_hash="ha",
            status=ProcessingStatus.PROCESSED,
            chunk_count=5,
            word_count=500,
        )
    )
    session.add(
        DocumentEmbeddingState(
            tenant_id="acme",
            document_id=doc.id,
            source_content_hash="ha",
            chunk_count=5,
            model="hashing-256",
        )
    )

    # Graph: an engineer modified the doc (ownership); a checkout service depends on ledger.
    doc_key = entity_key(EntityKind.DOCUMENT, str(doc.id))
    eng_key = entity_key(EntityKind.ENGINEER, "octocat")
    svc_key = entity_key(EntityKind.SERVICE, "checkout")
    ledger_key = entity_key(EntityKind.SERVICE, "ledger")
    for ent in (
        GraphEntity(tenant_id="acme", kind=EntityKind.ENGINEER, key=eng_key, name="octocat"),
        GraphEntity(tenant_id="acme", kind=EntityKind.DOCUMENT, key=doc_key, name=doc.title),
        GraphEntity(tenant_id="acme", kind=EntityKind.SERVICE, key=svc_key, name="checkout"),
        GraphEntity(tenant_id="acme", kind=EntityKind.SERVICE, key=ledger_key, name="ledger"),
    ):
        await graph.upsert_entity(ent)
    await graph.upsert_relationship(
        GraphRelationship(
            tenant_id="acme",
            type=RelationshipType.MODIFIED,
            from_key=eng_key,
            to_key=doc_key,
        )
    )
    await graph.upsert_relationship(
        GraphRelationship(
            tenant_id="acme",
            type=RelationshipType.DEPENDS_ON,
            from_key=svc_key,
            to_key=ledger_key,
        )
    )
    await session.flush()
    return doc.id


def _service(session: AsyncSession, graph: InMemoryGraphStore) -> AssistantService:
    chunk_repo = ChunkRepository(session)
    search = SearchService(HashingEmbedder(), InMemoryVectorStore(), chunk_repo, graph)
    trust = TrustService(TrustRepository(session), chunk_repo, graph)
    return AssistantService(search, trust, graph, ConversationRepository(session))


async def test_ask_persists_answer_with_trust(db_session: AsyncSession) -> None:
    graph = InMemoryGraphStore()
    await _seed(db_session, graph)
    service = _service(db_session, graph)

    conversation, message = await service.ask(
        "acme", "dev", "How does the checkout service work?"
    )

    assert message.role == MessageRole.ASSISTANT
    assert message.intent == AssistantIntent.SERVICE
    assert message.confidence is not None and message.confidence > 0
    assert message.answer_json is not None
    citations = message.answer_json["citations"]
    assert citations and citations[0]["title"] == "Checkout architecture"
    assert citations[0]["ownership_known"] is True

    detail = await service.get_conversation("acme", conversation.id)
    assert detail is not None
    _, messages = detail
    assert [m.role for m in messages] == [MessageRole.USER, MessageRole.ASSISTANT]


async def test_continue_conversation_appends(db_session: AsyncSession) -> None:
    graph = InMemoryGraphStore()
    await _seed(db_session, graph)
    service = _service(db_session, graph)

    conversation, _ = await service.ask("acme", "dev", "How does checkout work?")
    await service.ask("acme", "dev", "What does it depend on?", conversation.id)

    detail = await service.get_conversation("acme", conversation.id)
    assert detail is not None
    _, messages = detail
    assert len(messages) == 4  # two exchanges in the same conversation


async def test_ownership_question_surfaces_owner(db_session: AsyncSession) -> None:
    graph = InMemoryGraphStore()
    await _seed(db_session, graph)
    service = _service(db_session, graph)

    _, message = await service.ask("acme", "dev", "Who owns the checkout service?")
    assert message.intent == AssistantIntent.OWNERSHIP
    assert message.answer_json is not None
    assert "octocat" in message.content


async def test_list_conversations(db_session: AsyncSession) -> None:
    graph = InMemoryGraphStore()
    await _seed(db_session, graph)
    service = _service(db_session, graph)
    await service.ask("acme", "dev", "How does checkout work?")

    rows = await service.list_conversations("acme")
    assert len(rows) == 1
    conversation, count = rows[0]
    assert count == 2
    assert conversation.title


async def test_tenant_isolation(db_session: AsyncSession) -> None:
    graph = InMemoryGraphStore()
    await _seed(db_session, graph)
    service = _service(db_session, graph)
    conversation, _ = await service.ask("acme", "dev", "How does checkout work?")

    assert await service.get_conversation("other", conversation.id) is None
    assert await service.list_conversations("other") == []
