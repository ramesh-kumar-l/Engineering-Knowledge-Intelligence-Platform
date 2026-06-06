"""Retrieval primitives shared by the stores and services (Phase 4).

Frozen dataclasses keep the vector store, fusion and search service decoupled from
both the ORM and the Pydantic API schemas — the same layering the graph layer uses
(``app/graph/base.py``).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field

from app.domain.enums import EntityKind


@dataclass(frozen=True)
class VectorPoint:
    """A chunk embedded into the vector store."""

    tenant_id: str
    chunk_id: uuid.UUID
    document_id: uuid.UUID
    ordinal: int
    content: str
    title: str
    url: str | None
    vector: list[float]


@dataclass(frozen=True)
class VectorMatch:
    """A vector-search result with its similarity score."""

    chunk_id: uuid.UUID
    document_id: uuid.UUID
    ordinal: int
    content: str
    title: str
    url: str | None
    score: float


@dataclass(frozen=True)
class ChunkHit:
    """A ranked chunk in a search response (fused or single-retriever)."""

    chunk_id: uuid.UUID
    document_id: uuid.UUID
    ordinal: int
    title: str
    url: str | None
    snippet: str
    score: float
    keyword_rank: int | None = None
    vector_rank: int | None = None


@dataclass(frozen=True)
class EntityHit:
    """A knowledge-graph entity matching the query (graph facet)."""

    key: str
    kind: EntityKind
    name: str
    summary: str | None
    score: float


@dataclass(frozen=True)
class SearchResult:
    """The full hybrid retrieval result for one query."""

    query: str
    mode: str
    chunks: list[ChunkHit] = field(default_factory=list)
    entities: list[EntityHit] = field(default_factory=list)
