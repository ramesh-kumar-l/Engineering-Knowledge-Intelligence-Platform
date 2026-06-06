"""Qdrant client — vector store (ADR-0004).

Wraps the async Qdrant client. Phase 0 needs connectivity + a health probe;
collections/embeddings arrive in Phase 2/4.
"""

from __future__ import annotations

from qdrant_client import AsyncQdrantClient

from app.core.db.base import DataStoreStatus


class QdrantStore:
    name = "qdrant"

    def __init__(self, url: str) -> None:
        self._url = url
        self._client: AsyncQdrantClient | None = None

    async def connect(self) -> None:
        self._client = AsyncQdrantClient(url=self._url)

    async def close(self) -> None:
        if self._client is not None:
            await self._client.close()
            self._client = None

    @property
    def client(self) -> AsyncQdrantClient:
        """The connected client for the vector store (Phase 4). Raises if offline."""
        if self._client is None:
            raise RuntimeError("QdrantStore is not connected")
        return self._client

    async def health_check(self) -> DataStoreStatus:
        if self._client is None:
            return DataStoreStatus(self.name, healthy=False, detail="not connected")
        try:
            await self._client.get_collections()
            return DataStoreStatus(self.name, healthy=True)
        except Exception as exc:  # noqa: BLE001 - surfaced as readiness detail
            return DataStoreStatus(self.name, healthy=False, detail=str(exc))
