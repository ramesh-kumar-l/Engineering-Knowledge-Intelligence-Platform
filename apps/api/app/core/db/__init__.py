"""Datastore clients (ADR-0004): PostgreSQL, Neo4j, Qdrant.

Each client exposes ``connect`` / ``close`` / ``health_check`` behind a common
``DataStore`` protocol so the rest of the app depends on the abstraction, not the
driver. The ``DataStores`` registry wires them into the app lifespan.
"""

from app.core.db.base import DataStore, DataStoreStatus
from app.core.db.registry import DataStores

__all__ = ["DataStore", "DataStoreStatus", "DataStores"]
