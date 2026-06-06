"""Qdrant-backed :class:`~app.retrieval.vector_store.VectorStore` (ADR-0004/0015).

One shared collection holds every tenant's chunk vectors; isolation is enforced by a
mandatory ``tenant_id`` payload filter on every search and delete. Point ids are chunk
UUIDs, so re-embedding a chunk overwrites in place. Like the Cypher graph store, this
thin adapter is exercised by integration runs rather than unit tests — the in-memory
store stands in for the suite (ADR-0015).
"""

from __future__ import annotations

import uuid

from qdrant_client import models

from app.core.db.qdrant import QdrantStore
from app.retrieval.base import VectorMatch, VectorPoint

_COLLECTION = "ekip_chunks"


class QdrantVectorStore:
    def __init__(self, store: QdrantStore) -> None:
        self._store = store

    @property
    def _client(self):  # type: ignore[no-untyped-def]
        return self._store.client

    async def ensure_collection(self, dimension: int) -> None:
        if await self._client.collection_exists(_COLLECTION):
            return
        await self._client.create_collection(
            collection_name=_COLLECTION,
            vectors_config=models.VectorParams(
                size=dimension, distance=models.Distance.COSINE
            ),
        )
        await self._client.create_payload_index(
            collection_name=_COLLECTION,
            field_name="tenant_id",
            field_schema=models.PayloadSchemaType.KEYWORD,
        )

    async def upsert(self, points: list[VectorPoint]) -> None:
        if not points:
            return
        await self._client.upsert(
            collection_name=_COLLECTION,
            points=[
                models.PointStruct(
                    id=str(point.chunk_id),
                    vector=point.vector,
                    payload={
                        "tenant_id": point.tenant_id,
                        "document_id": str(point.document_id),
                        "ordinal": point.ordinal,
                        "content": point.content,
                        "title": point.title,
                        "url": point.url,
                    },
                )
                for point in points
            ],
        )

    async def delete_document(self, tenant_id: str, document_id: uuid.UUID) -> None:
        await self._client.delete(
            collection_name=_COLLECTION,
            points_selector=models.FilterSelector(filter=self._doc_filter(tenant_id, document_id)),
        )

    async def search(
        self, tenant_id: str, vector: list[float], limit: int = 10
    ) -> list[VectorMatch]:
        response = await self._client.query_points(
            collection_name=_COLLECTION,
            query=vector,
            query_filter=self._tenant_filter(tenant_id),
            limit=limit,
            with_payload=True,
        )
        return [self._to_match(p) for p in response.points]

    async def count(self, tenant_id: str) -> int:
        result = await self._client.count(
            collection_name=_COLLECTION,
            count_filter=self._tenant_filter(tenant_id),
            exact=True,
        )
        return int(result.count)

    @staticmethod
    def _tenant_filter(tenant_id: str) -> models.Filter:
        return models.Filter(
            must=[
                models.FieldCondition(
                    key="tenant_id", match=models.MatchValue(value=tenant_id)
                )
            ]
        )

    @staticmethod
    def _doc_filter(tenant_id: str, document_id: uuid.UUID) -> models.Filter:
        return models.Filter(
            must=[
                models.FieldCondition(
                    key="tenant_id", match=models.MatchValue(value=tenant_id)
                ),
                models.FieldCondition(
                    key="document_id", match=models.MatchValue(value=str(document_id))
                ),
            ]
        )

    @staticmethod
    def _to_match(point: models.ScoredPoint) -> VectorMatch:
        payload = point.payload or {}
        return VectorMatch(
            chunk_id=uuid.UUID(str(point.id)),
            document_id=uuid.UUID(payload["document_id"]),
            ordinal=int(payload.get("ordinal", 0)),
            content=payload.get("content", ""),
            title=payload.get("title", ""),
            url=payload.get("url"),
            score=float(point.score),
        )
