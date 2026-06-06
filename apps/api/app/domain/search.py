"""Search API schemas (mirrored in packages/contracts)."""

from __future__ import annotations

import uuid
from typing import Literal

from pydantic import BaseModel

from app.domain.enums import EntityKind
from app.retrieval.base import ChunkHit, EntityHit, SearchResult

SearchMode = Literal["keyword", "vector", "hybrid"]


class SearchChunkHit(BaseModel):
    chunk_id: uuid.UUID
    document_id: uuid.UUID
    ordinal: int
    title: str
    url: str | None
    snippet: str
    score: float
    keyword_rank: int | None
    vector_rank: int | None

    @classmethod
    def from_hit(cls, hit: ChunkHit) -> SearchChunkHit:
        return cls(
            chunk_id=hit.chunk_id,
            document_id=hit.document_id,
            ordinal=hit.ordinal,
            title=hit.title,
            url=hit.url,
            snippet=hit.snippet,
            score=hit.score,
            keyword_rank=hit.keyword_rank,
            vector_rank=hit.vector_rank,
        )


class SearchEntityHit(BaseModel):
    key: str
    kind: EntityKind
    name: str
    summary: str | None
    score: float

    @classmethod
    def from_hit(cls, hit: EntityHit) -> SearchEntityHit:
        return cls(
            key=hit.key,
            kind=hit.kind,
            name=hit.name,
            summary=hit.summary,
            score=hit.score,
        )


class SearchResponse(BaseModel):
    query: str
    mode: SearchMode
    chunks: list[SearchChunkHit]
    entities: list[SearchEntityHit]

    @classmethod
    def from_result(cls, result: SearchResult) -> SearchResponse:
        mode: SearchMode = result.mode  # type: ignore[assignment]
        return cls(
            query=result.query,
            mode=mode,
            chunks=[SearchChunkHit.from_hit(c) for c in result.chunks],
            entities=[SearchEntityHit.from_hit(e) for e in result.entities],
        )
