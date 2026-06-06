"""Neo4j client — knowledge graph (ADR-0004).

Wraps the official async driver. Phase 0 needs connectivity + a health probe; graph
schema (entities/relationships) arrives in Phase 3.
"""

from __future__ import annotations

from neo4j import AsyncDriver, AsyncGraphDatabase

from app.core.db.base import DataStoreStatus


class Neo4jStore:
    name = "neo4j"

    def __init__(self, uri: str, user: str, password: str) -> None:
        self._uri = uri
        self._auth = (user, password)
        self._driver: AsyncDriver | None = None

    async def connect(self) -> None:
        self._driver = AsyncGraphDatabase.driver(self._uri, auth=self._auth)

    async def close(self) -> None:
        if self._driver is not None:
            await self._driver.close()
            self._driver = None

    async def health_check(self) -> DataStoreStatus:
        if self._driver is None:
            return DataStoreStatus(self.name, healthy=False, detail="not connected")
        try:
            await self._driver.verify_connectivity()
            return DataStoreStatus(self.name, healthy=True)
        except Exception as exc:  # noqa: BLE001 - surfaced as readiness detail
            return DataStoreStatus(self.name, healthy=False, detail=str(exc))
