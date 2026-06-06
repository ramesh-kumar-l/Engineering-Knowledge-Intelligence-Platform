"""InMemoryVectorStore tests — upsert/search/delete, tenant isolation."""

from __future__ import annotations

import uuid

from app.retrieval.base import VectorPoint
from app.retrieval.vector_store import InMemoryVectorStore


def _point(tenant: str, vector: list[float], doc: uuid.UUID | None = None) -> VectorPoint:
    return VectorPoint(
        tenant_id=tenant,
        chunk_id=uuid.uuid4(),
        document_id=doc or uuid.uuid4(),
        ordinal=0,
        content="content",
        title="title",
        url=None,
        vector=vector,
    )


async def test_search_orders_by_similarity() -> None:
    store = InMemoryVectorStore()
    near = _point("acme", [1.0, 0.0])
    far = _point("acme", [0.0, 1.0])
    await store.upsert([near, far])

    results = await store.search("acme", [1.0, 0.0], limit=2)
    assert results[0].chunk_id == near.chunk_id
    assert results[0].score > results[1].score


async def test_delete_document_removes_points() -> None:
    store = InMemoryVectorStore()
    doc = uuid.uuid4()
    await store.upsert([_point("acme", [1.0, 0.0], doc), _point("acme", [0.0, 1.0], doc)])
    await store.delete_document("acme", doc)
    assert await store.count("acme") == 0


async def test_tenant_isolation() -> None:
    store = InMemoryVectorStore()
    await store.upsert([_point("acme", [1.0, 0.0])])
    await store.upsert([_point("other", [1.0, 0.0])])
    assert await store.count("acme") == 1
    assert await store.count("other") == 1
    assert len(await store.search("acme", [1.0, 0.0])) == 1
