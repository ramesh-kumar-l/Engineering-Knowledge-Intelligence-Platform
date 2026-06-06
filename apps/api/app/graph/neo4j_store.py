"""Neo4j-backed :class:`~app.graph.store.GraphStore` (ADR-0004/0012).

Nodes share the ``:Entity`` label with a ``kind`` property (one uniqueness constraint
covers all kinds); relationships use typed edges. The relationship type is taken from
the :class:`RelationshipType` enum member name, so interpolating it into Cypher is safe
(never user input). Every query is filtered by ``tenant_id`` for isolation.
"""

from __future__ import annotations

from typing import Any

from app.core.db.neo4j import Neo4jStore
from app.domain.enums import EntityKind, GraphSource, RelationshipType
from app.graph.base import (
    GraphEntity,
    GraphNeighbor,
    GraphNeighborhood,
    GraphRelationship,
    GraphStats,
)


def _to_entity(props: dict[str, Any]) -> GraphEntity:
    return GraphEntity(
        tenant_id=props["tenant_id"],
        kind=EntityKind(props["kind"]),
        key=props["key"],
        name=props["name"],
        source=GraphSource(props.get("source", GraphSource.PROJECTION.value)),
        summary=props.get("summary"),
        url=props.get("url"),
        category=props.get("category"),
    )


class Neo4jGraphStore:
    def __init__(self, store: Neo4jStore) -> None:
        self._store = store

    async def _run(self, cypher: str, params: dict[str, Any]) -> list[dict[str, Any]]:
        async with self._store.driver.session() as session:
            result = await session.run(cypher, params)
            return [record async for record in result]  # type: ignore[misc]

    async def ensure_schema(self) -> None:
        await self._run(
            "CREATE CONSTRAINT entity_key IF NOT EXISTS "
            "FOR (n:Entity) REQUIRE (n.tenant_id, n.key) IS UNIQUE",
            {},
        )

    async def upsert_entity(self, entity: GraphEntity) -> None:
        await self._run(
            "MERGE (n:Entity {tenant_id: $tenant_id, key: $key}) "
            "SET n.kind=$kind, n.name=$name, n.source=$source, "
            "n.summary=$summary, n.url=$url, n.category=$category",
            {
                "tenant_id": entity.tenant_id,
                "key": entity.key,
                "kind": entity.kind.value,
                "name": entity.name,
                "source": entity.source.value,
                "summary": entity.summary,
                "url": entity.url,
                "category": entity.category,
            },
        )

    async def upsert_relationship(self, rel: GraphRelationship) -> None:
        # rel.type.name is enum-controlled (e.g. DEPENDS_ON); safe to interpolate.
        await self._run(
            "MATCH (a:Entity {tenant_id: $t, key: $from_key}) "
            "MATCH (b:Entity {tenant_id: $t, key: $to_key}) "
            f"MERGE (a)-[r:`{rel.type.name}`]->(b) "
            "SET r.tenant_id=$t, r.source=$source",
            {
                "t": rel.tenant_id,
                "from_key": rel.from_key,
                "to_key": rel.to_key,
                "source": rel.source.value,
            },
        )

    async def get_entity(self, tenant_id: str, key: str) -> GraphEntity | None:
        rows = await self._run(
            "MATCH (n:Entity {tenant_id: $t, key: $key}) RETURN n",
            {"t": tenant_id, "key": key},
        )
        return _to_entity(dict(rows[0]["n"])) if rows else None

    async def list_entities(
        self,
        tenant_id: str,
        kind: EntityKind | None = None,
        search: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[GraphEntity]:
        rows = await self._run(
            "MATCH (n:Entity {tenant_id: $t}) "
            "WHERE ($kind IS NULL OR n.kind=$kind) AND "
            "($needle IS NULL OR toLower(n.name) CONTAINS $needle "
            "OR toLower(n.key) CONTAINS $needle) "
            "RETURN n ORDER BY n.kind, toLower(n.name) SKIP $offset LIMIT $limit",
            {
                "t": tenant_id,
                "kind": kind.value if kind else None,
                "needle": search.lower() if search else None,
                "offset": offset,
                "limit": limit,
            },
        )
        return [_to_entity(dict(r["n"])) for r in rows]

    async def neighborhood(
        self, tenant_id: str, key: str
    ) -> GraphNeighborhood | None:
        rows = await self._run(
            "MATCH (n:Entity {tenant_id: $t, key: $key}) "
            "OPTIONAL MATCH (n)-[r]-(m:Entity {tenant_id: $t}) "
            "RETURN n, type(r) AS rel_type, m, startNode(r).key = n.key AS outgoing",
            {"t": tenant_id, "key": key},
        )
        if not rows:
            return None
        focus = _to_entity(dict(rows[0]["n"]))
        neighbors: list[GraphNeighbor] = []
        for r in rows:
            if r["m"] is None or r["rel_type"] is None:
                continue
            neighbors.append(
                GraphNeighbor(
                    type=RelationshipType[r["rel_type"]],
                    direction="out" if r["outgoing"] else "in",
                    entity=_to_entity(dict(r["m"])),
                )
            )
        neighbors.sort(key=lambda n: (n.type.value, n.direction, n.entity.name.lower()))
        return GraphNeighborhood(entity=focus, neighbors=neighbors)

    async def list_relationships(
        self,
        tenant_id: str,
        type: RelationshipType | None = None,
        limit: int = 200,
    ) -> list[GraphRelationship]:
        rows = await self._run(
            "MATCH (a:Entity {tenant_id: $t})-[r]->(b:Entity {tenant_id: $t}) "
            "WHERE ($type IS NULL OR type(r)=$type) "
            "RETURN a, type(r) AS rel_type, b ORDER BY type(r), a.key, b.key LIMIT $limit",
            {"t": tenant_id, "type": type.name if type else None, "limit": limit},
        )
        out: list[GraphRelationship] = []
        for r in rows:
            a, b = _to_entity(dict(r["a"])), _to_entity(dict(r["b"]))
            out.append(
                GraphRelationship(
                    tenant_id=tenant_id,
                    type=RelationshipType[r["rel_type"]],
                    from_key=a.key,
                    to_key=b.key,
                    from_kind=a.kind,
                    from_name=a.name,
                    to_kind=b.kind,
                    to_name=b.name,
                )
            )
        return out

    async def stats(self, tenant_id: str) -> GraphStats:
        kinds = await self._run(
            "MATCH (n:Entity {tenant_id: $t}) RETURN n.kind AS kind, count(*) AS c",
            {"t": tenant_id},
        )
        rels = await self._run(
            "MATCH (:Entity {tenant_id: $t})-[r]->(:Entity {tenant_id: $t}) "
            "RETURN type(r) AS rel_type, count(*) AS c",
            {"t": tenant_id},
        )
        return GraphStats(
            entities_by_kind={r["kind"]: r["c"] for r in kinds},
            relationships_by_type={
                RelationshipType[r["rel_type"]].value: r["c"] for r in rels
            },
        )
