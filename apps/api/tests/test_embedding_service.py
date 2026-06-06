"""Embedding engine tests — index build, staleness skip, force (SQLite + memory store)."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.enums import SourceType, SyncStatus
from app.models.chunk import Chunk
from app.models.connector import Connector
from app.models.document import Document
from app.repositories.chunks import ChunkRepository
from app.repositories.embedding import EmbeddingRepository
from app.retrieval.embedder import HashingEmbedder
from app.retrieval.embedding_service import EmbeddingService
from app.retrieval.vector_store import InMemoryVectorStore


def _service(session: AsyncSession, store: InMemoryVectorStore) -> EmbeddingService:
    return EmbeddingService(
        EmbeddingRepository(session),
        ChunkRepository(session),
        HashingEmbedder(dimension=64),
        store,
    )


async def _seed(session: AsyncSession, content_hash: str = "h1") -> Document:
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
        title="Payment incident",
        content_hash=content_hash,
        raw_content="body",
    )
    session.add(doc)
    await session.flush()
    for ordinal in range(2):
        session.add(
            Chunk(
                tenant_id="acme",
                document_id=doc.id,
                ordinal=ordinal,
                content=f"chunk {ordinal} about payments",
                content_hash=f"c{ordinal}",
            )
        )
    await session.flush()
    return doc


async def test_embed_indexes_chunks(db_session: AsyncSession) -> None:
    await _seed(db_session)
    store = InMemoryVectorStore()

    run = await _service(db_session, store).embed("acme")
    assert run.status == SyncStatus.SUCCEEDED
    assert run.documents_embedded == 1
    assert run.chunk_count == 2
    assert await store.count("acme") == 2


async def test_reembed_skips_unchanged(db_session: AsyncSession) -> None:
    await _seed(db_session)
    store = InMemoryVectorStore()
    service = _service(db_session, store)

    await service.embed("acme")
    second = await service.embed("acme")
    assert second.documents_embedded == 0
    assert second.documents_skipped == 1
    assert await store.count("acme") == 2


async def test_force_reembeds(db_session: AsyncSession) -> None:
    await _seed(db_session)
    store = InMemoryVectorStore()
    service = _service(db_session, store)

    await service.embed("acme")
    forced = await service.embed("acme", force=True)
    assert forced.documents_embedded == 1
    assert await store.count("acme") == 2  # replaced, not duplicated
