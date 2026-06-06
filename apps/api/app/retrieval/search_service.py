"""Hybrid search engine (Phase 4).

Answers a query with three retrievers and fuses the text ones:
- **keyword** — candidate chunks via a portable ``LIKE``, ranked deterministically;
- **vector** — the query embedded and matched against the vector store;
- **graph** — knowledge-graph entities whose name/key match the query (a facet).

``mode`` selects ``keyword``, ``vector`` or ``hybrid`` (reciprocal-rank fusion of the
two text retrievers; ADR-0016). The graph facet is always included — it is cheap and
complements the chunk results with structured context.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from app.graph.store import GraphStore
from app.repositories.chunks import ChunkRepository
from app.retrieval import keyword
from app.retrieval.base import ChunkHit, EntityHit, SearchResult
from app.retrieval.embedder import Embedder
from app.retrieval.fusion import reciprocal_rank_fusion
from app.retrieval.vector_store import VectorStore

_CANDIDATES = 50
_SNIPPET_CHARS = 240


@dataclass
class _ChunkMeta:
    document_id: uuid.UUID
    ordinal: int
    title: str
    url: str | None
    content: str


class SearchService:
    def __init__(
        self,
        embedder: Embedder,
        vector_store: VectorStore,
        chunk_repo: ChunkRepository,
        graph_store: GraphStore,
    ) -> None:
        self._embedder = embedder
        self._store = vector_store
        self._chunks = chunk_repo
        self._graph = graph_store

    async def search(
        self,
        tenant_id: str,
        query: str,
        mode: str = "hybrid",
        limit: int = 10,
    ) -> SearchResult:
        query = query.strip()
        if not query:
            return SearchResult(query=query, mode=mode)

        meta: dict[uuid.UUID, _ChunkMeta] = {}
        keyword_ids = await self._keyword(tenant_id, query, meta)
        vector_ids = (
            await self._vector(tenant_id, query, meta)
            if mode in ("vector", "hybrid")
            else []
        )
        if mode == "keyword":
            vector_ids = []

        ranked = self._rank(mode, keyword_ids, vector_ids)
        kw_rank = {cid: i for i, cid in enumerate(keyword_ids)}
        vec_rank = {cid: i for i, cid in enumerate(vector_ids)}

        chunks = [
            ChunkHit(
                chunk_id=cid,
                document_id=meta[cid].document_id,
                ordinal=meta[cid].ordinal,
                title=meta[cid].title,
                url=meta[cid].url,
                snippet=_snippet(meta[cid].content),
                score=round(score, 6),
                keyword_rank=kw_rank.get(cid),
                vector_rank=vec_rank.get(cid),
            )
            for cid, score in ranked
            if cid in meta
        ][:limit]

        entities = await self._entities(tenant_id, query, limit)
        return SearchResult(query=query, mode=mode, chunks=chunks, entities=entities)

    async def _keyword(
        self, tenant_id: str, query: str, meta: dict[uuid.UUID, _ChunkMeta]
    ) -> list[uuid.UUID]:
        terms = keyword.query_terms(query)
        candidates = await self._chunks.search_candidates(tenant_id, terms, _CANDIDATES)
        scored: list[tuple[uuid.UUID, float]] = []
        for chunk, document in candidates:
            meta.setdefault(
                chunk.id,
                _ChunkMeta(
                    document_id=document.id,
                    ordinal=chunk.ordinal,
                    title=document.title,
                    url=document.url,
                    content=chunk.content,
                ),
            )
            scored.append((chunk.id, keyword.score(chunk.content, document.title, terms)))
        scored.sort(key=lambda kv: (-kv[1], str(kv[0])))
        return [cid for cid, _ in scored]

    async def _vector(
        self, tenant_id: str, query: str, meta: dict[uuid.UUID, _ChunkMeta]
    ) -> list[uuid.UUID]:
        vector = self._embedder.embed(query)
        matches = await self._store.search(tenant_id, vector, _CANDIDATES)
        for match in matches:
            meta.setdefault(
                match.chunk_id,
                _ChunkMeta(
                    document_id=match.document_id,
                    ordinal=match.ordinal,
                    title=match.title,
                    url=match.url,
                    content=match.content,
                ),
            )
        return [m.chunk_id for m in matches]

    def _rank(
        self,
        mode: str,
        keyword_ids: list[uuid.UUID],
        vector_ids: list[uuid.UUID],
    ) -> list[tuple[uuid.UUID, float]]:
        if mode == "keyword":
            return [(cid, 1.0 / (i + 1)) for i, cid in enumerate(keyword_ids)]
        if mode == "vector":
            return [(cid, 1.0 / (i + 1)) for i, cid in enumerate(vector_ids)]
        return reciprocal_rank_fusion([keyword_ids, vector_ids])

    async def _entities(
        self, tenant_id: str, query: str, limit: int
    ) -> list[EntityHit]:
        entities = await self._graph.list_entities(
            tenant_id, search=query, limit=limit
        )
        return [
            EntityHit(
                key=e.key,
                kind=e.kind,
                name=e.name,
                summary=e.summary,
                score=round(1.0 / (i + 1), 6),
            )
            for i, e in enumerate(entities)
        ]


def _snippet(content: str) -> str:
    text = " ".join(content.split())
    return text[:_SNIPPET_CHARS] + ("…" if len(text) > _SNIPPET_CHARS else "")
