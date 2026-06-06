"""Vector store abstraction (ADR-0015).

Embeddings live in Qdrant in production (``qdrant_store.QdrantVectorStore``).
``VectorStore`` is the seam that keeps the services free of driver details and lets the
``InMemoryVectorStore`` below back fast, offline tests — the same role SQLite plays for
PostgreSQL and ``InMemoryGraphStore`` plays for Neo4j. Every operation is tenant-scoped.
"""

from __future__ import annotations

import math
import uuid
from typing import Protocol, runtime_checkable

from app.retrieval.base import VectorMatch, VectorPoint


@runtime_checkable
class VectorStore(Protocol):
    """Tenant-scoped persistence + similarity search for chunk embeddings."""

    async def ensure_collection(self, dimension: int) -> None: ...

    async def upsert(self, points: list[VectorPoint]) -> None: ...

    async def delete_document(self, tenant_id: str, document_id: uuid.UUID) -> None: ...

    async def search(
        self, tenant_id: str, vector: list[float], limit: int = 10
    ) -> list[VectorMatch]: ...

    async def count(self, tenant_id: str) -> int: ...


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b, strict=False))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0.0 or nb == 0.0:
        return 0.0
    return dot / (na * nb)


class InMemoryVectorStore:
    """Dict-backed vector store for tests and Qdrant-free local runs.

    Points are keyed by chunk id, so re-embedding a chunk overwrites rather than
    duplicating; ``delete_document`` clears a document's points before re-upsert, which
    matches the wholesale chunk replacement done on reprocessing.
    """

    def __init__(self) -> None:
        self._points: dict[uuid.UUID, VectorPoint] = {}

    async def ensure_collection(self, dimension: int) -> None:
        return None

    async def upsert(self, points: list[VectorPoint]) -> None:
        for point in points:
            self._points[point.chunk_id] = point

    async def delete_document(self, tenant_id: str, document_id: uuid.UUID) -> None:
        for chunk_id, point in list(self._points.items()):
            if point.tenant_id == tenant_id and point.document_id == document_id:
                del self._points[chunk_id]

    async def search(
        self, tenant_id: str, vector: list[float], limit: int = 10
    ) -> list[VectorMatch]:
        scored = [
            VectorMatch(
                chunk_id=point.chunk_id,
                document_id=point.document_id,
                ordinal=point.ordinal,
                content=point.content,
                title=point.title,
                url=point.url,
                score=_cosine(vector, point.vector),
            )
            for point in self._points.values()
            if point.tenant_id == tenant_id
        ]
        scored.sort(key=lambda m: (-m.score, str(m.chunk_id)))
        return scored[:limit]

    async def count(self, tenant_id: str) -> int:
        return sum(1 for p in self._points.values() if p.tenant_id == tenant_id)
