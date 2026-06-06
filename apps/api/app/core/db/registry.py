"""Datastore protocol + registry.

The registry owns the lifecycle of all stores and aggregates their health for the
readiness probe. Keeping this in one small module lets routes/lifespan depend on the
abstraction rather than concrete drivers.
"""

from __future__ import annotations

import asyncio

from app.core.config import Settings
from app.core.db.base import DataStore, DataStoreStatus
from app.core.db.neo4j import Neo4jStore
from app.core.db.postgres import PostgresStore
from app.core.db.qdrant import QdrantStore


class DataStores:
    """Owns and coordinates all datastore clients."""

    def __init__(self, settings: Settings) -> None:
        self.postgres = PostgresStore(settings.postgres_dsn)
        self.neo4j = Neo4jStore(
            settings.neo4j_uri, settings.neo4j_user, settings.neo4j_password
        )
        self.qdrant = QdrantStore(settings.qdrant_url)

    @property
    def all(self) -> tuple[DataStore, ...]:
        return (self.postgres, self.neo4j, self.qdrant)

    async def connect(self) -> None:
        """Open all connections concurrently. Tolerant: connection is lazy/pooled,
        so a store being down does not crash startup — readiness reports it instead."""
        await asyncio.gather(*(s.connect() for s in self.all), return_exceptions=True)

    async def close(self) -> None:
        await asyncio.gather(*(s.close() for s in self.all), return_exceptions=True)

    async def health_check(self) -> list[DataStoreStatus]:
        """Probe every store concurrently for the readiness endpoint."""
        results = await asyncio.gather(
            *(s.health_check() for s in self.all), return_exceptions=True
        )
        statuses: list[DataStoreStatus] = []
        for store, result in zip(self.all, results, strict=True):
            if isinstance(result, DataStoreStatus):
                statuses.append(result)
            else:
                statuses.append(
                    DataStoreStatus(name=store.name, healthy=False, detail=str(result))
                )
        return statuses
