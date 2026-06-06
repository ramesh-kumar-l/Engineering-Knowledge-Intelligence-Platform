"""Hybrid search tests — keyword/vector/hybrid + graph facet (SQLite + memory stores)."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.enums import EntityKind, GraphSource, SourceType
from app.graph.base import GraphEntity, entity_key, slugify
from app.graph.store import InMemoryGraphStore
from app.models.chunk import Chunk
from app.models.connector import Connector
from app.models.document import Document
from app.repositories.chunks import ChunkRepository
from app.repositories.embedding import EmbeddingRepository
from app.retrieval.embedder import HashingEmbedder
from app.retrieval.embedding_service import EmbeddingService
from app.retrieval.search_service import SearchService
from app.retrieval.vector_store import InMemoryVectorStore


async def _seed_corpus(session: AsyncSession) -> None:
    connector = Connector(
        tenant_id="acme",
        source_type=SourceType.GITHUB,
        name="repo",
        config={"owner": "octo", "repo": "app"},
    )
    session.add(connector)
    await session.flush()
    docs = {
        "Payment outage postmortem": "the payment service returned errors during checkout",
        "Frontend theme tokens": "button colors and spacing tokens for dark mode",
    }
    for i, (title, body) in enumerate(docs.items()):
        doc = Document(
            tenant_id="acme",
            connector_id=connector.id,
            source_type=SourceType.GITHUB,
            external_id=str(i),
            title=title,
            content_hash=f"h{i}",
            raw_content=body,
        )
        session.add(doc)
        await session.flush()
        session.add(
            Chunk(
                tenant_id="acme",
                document_id=doc.id,
                ordinal=0,
                content=body,
                content_hash=f"c{i}",
            )
        )
    await session.flush()


def _search_service(
    session: AsyncSession,
    vector_store: InMemoryVectorStore,
    graph_store: InMemoryGraphStore,
) -> SearchService:
    return SearchService(
        HashingEmbedder(dimension=64),
        vector_store,
        ChunkRepository(session),
        graph_store,
    )


async def test_keyword_search_finds_relevant_doc(db_session: AsyncSession) -> None:
    await _seed_corpus(db_session)
    service = _search_service(db_session, InMemoryVectorStore(), InMemoryGraphStore())

    result = await service.search("acme", "payment checkout", mode="keyword")
    assert result.chunks
    assert "payment" in result.chunks[0].title.lower()


async def test_hybrid_search_includes_vector_and_graph(db_session: AsyncSession) -> None:
    await _seed_corpus(db_session)
    vector_store = InMemoryVectorStore()
    graph_store = InMemoryGraphStore()
    await EmbeddingService(
        EmbeddingRepository(db_session),
        ChunkRepository(db_session),
        HashingEmbedder(dimension=64),
        vector_store,
    ).embed("acme")
    await graph_store.upsert_entity(
        GraphEntity(
            tenant_id="acme",
            kind=EntityKind.SERVICE,
            key=entity_key(EntityKind.SERVICE, slugify("Payment Service")),
            name="Payment Service",
            source=GraphSource.MANUAL,
        )
    )

    service = _search_service(db_session, vector_store, graph_store)
    result = await service.search("acme", "payment", mode="hybrid")
    assert result.chunks
    assert result.chunks[0].vector_rank is not None
    assert any(e.name == "Payment Service" for e in result.entities)


async def test_blank_query_returns_empty(db_session: AsyncSession) -> None:
    service = _search_service(db_session, InMemoryVectorStore(), InMemoryGraphStore())
    result = await service.search("acme", "   ", mode="hybrid")
    assert result.chunks == []
    assert result.entities == []
