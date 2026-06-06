"""Graph store abstraction (ADR-0012).

The knowledge graph lives in Neo4j in production (``neo4j_store.Neo4jGraphStore``).
``GraphStore`` is the seam that keeps the service free of driver details and lets the
in-memory implementation below back fast, offline tests — the same role SQLite plays
for the PostgreSQL repositories. Every operation is tenant-scoped.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from app.domain.enums import EntityKind, RelationshipType
from app.graph.base import (
    GraphEntity,
    GraphNeighbor,
    GraphNeighborhood,
    GraphRelationship,
    GraphStats,
)


@runtime_checkable
class GraphStore(Protocol):
    """Tenant-scoped persistence for graph entities and relationships."""

    async def ensure_schema(self) -> None: ...

    async def upsert_entity(self, entity: GraphEntity) -> None: ...

    async def upsert_relationship(self, rel: GraphRelationship) -> None: ...

    async def get_entity(self, tenant_id: str, key: str) -> GraphEntity | None: ...

    async def list_entities(
        self,
        tenant_id: str,
        kind: EntityKind | None = None,
        search: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[GraphEntity]: ...

    async def neighborhood(
        self, tenant_id: str, key: str
    ) -> GraphNeighborhood | None: ...

    async def list_relationships(
        self,
        tenant_id: str,
        type: RelationshipType | None = None,
        limit: int = 200,
    ) -> list[GraphRelationship]: ...

    async def stats(self, tenant_id: str) -> GraphStats: ...


def _rel_id(rel: GraphRelationship) -> tuple[str, str, str, str]:
    return (rel.tenant_id, rel.type.value, rel.from_key, rel.to_key)


class InMemoryGraphStore:
    """Dict-backed graph store for tests and Neo4j-free local runs.

    Upserts are idempotent (keyed by tenant+key for nodes, tenant+type+endpoints for
    edges), so re-running a projection converges rather than duplicating.
    """

    def __init__(self) -> None:
        self._entities: dict[tuple[str, str], GraphEntity] = {}
        self._relationships: dict[tuple[str, str, str, str], GraphRelationship] = {}

    async def ensure_schema(self) -> None:
        return None

    async def upsert_entity(self, entity: GraphEntity) -> None:
        self._entities[(entity.tenant_id, entity.key)] = entity

    async def upsert_relationship(self, rel: GraphRelationship) -> None:
        self._relationships[_rel_id(rel)] = rel

    async def get_entity(self, tenant_id: str, key: str) -> GraphEntity | None:
        return self._entities.get((tenant_id, key))

    async def list_entities(
        self,
        tenant_id: str,
        kind: EntityKind | None = None,
        search: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[GraphEntity]:
        needle = search.lower() if search else None
        rows = [
            e
            for (t, _), e in self._entities.items()
            if t == tenant_id
            and (kind is None or e.kind == kind)
            and (needle is None or needle in e.name.lower() or needle in e.key.lower())
        ]
        rows.sort(key=lambda e: (e.kind.value, e.name.lower()))
        return rows[offset : offset + limit]

    async def neighborhood(
        self, tenant_id: str, key: str
    ) -> GraphNeighborhood | None:
        focus = self._entities.get((tenant_id, key))
        if focus is None:
            return None
        neighbors: list[GraphNeighbor] = []
        for rel in self._relationships.values():
            if rel.tenant_id != tenant_id:
                continue
            if rel.from_key == key:
                other = self._entities.get((tenant_id, rel.to_key))
                if other is not None:
                    neighbors.append(GraphNeighbor(rel.type, "out", other))
            elif rel.to_key == key:
                other = self._entities.get((tenant_id, rel.from_key))
                if other is not None:
                    neighbors.append(GraphNeighbor(rel.type, "in", other))
        neighbors.sort(key=lambda n: (n.type.value, n.direction, n.entity.name.lower()))
        return GraphNeighborhood(entity=focus, neighbors=neighbors)

    async def list_relationships(
        self,
        tenant_id: str,
        type: RelationshipType | None = None,
        limit: int = 200,
    ) -> list[GraphRelationship]:
        rows: list[GraphRelationship] = []
        for rel in self._relationships.values():
            if rel.tenant_id != tenant_id or (type is not None and rel.type != type):
                continue
            rows.append(self._with_endpoints(rel))
        rows.sort(key=lambda r: (r.type.value, r.from_key, r.to_key))
        return rows[:limit]

    async def stats(self, tenant_id: str) -> GraphStats:
        by_kind: dict[str, int] = {}
        for (t, _), e in self._entities.items():
            if t == tenant_id:
                by_kind[e.kind.value] = by_kind.get(e.kind.value, 0) + 1
        by_type: dict[str, int] = {}
        for rel in self._relationships.values():
            if rel.tenant_id == tenant_id:
                by_type[rel.type.value] = by_type.get(rel.type.value, 0) + 1
        return GraphStats(entities_by_kind=by_kind, relationships_by_type=by_type)

    def _with_endpoints(self, rel: GraphRelationship) -> GraphRelationship:
        src = self._entities.get((rel.tenant_id, rel.from_key))
        dst = self._entities.get((rel.tenant_id, rel.to_key))
        return GraphRelationship(
            tenant_id=rel.tenant_id,
            type=rel.type,
            from_key=rel.from_key,
            to_key=rel.to_key,
            source=rel.source,
            from_kind=src.kind if src else None,
            from_name=src.name if src else None,
            to_kind=dst.kind if dst else None,
            to_name=dst.name if dst else None,
        )
