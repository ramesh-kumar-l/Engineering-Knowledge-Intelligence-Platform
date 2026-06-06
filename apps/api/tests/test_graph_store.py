"""InMemoryGraphStore tests — upsert, neighborhood, stats, tenant isolation."""

from __future__ import annotations

from app.domain.enums import EntityKind, GraphSource, RelationshipType
from app.graph.base import GraphEntity, GraphRelationship
from app.graph.store import InMemoryGraphStore


def _entity(tenant: str, kind: EntityKind, key: str, name: str) -> GraphEntity:
    return GraphEntity(tenant_id=tenant, kind=kind, key=key, name=name)


async def _seed(store: InMemoryGraphStore, tenant: str = "acme") -> None:
    await store.upsert_entity(_entity(tenant, EntityKind.SERVICE, "service:a", "A"))
    await store.upsert_entity(_entity(tenant, EntityKind.SERVICE, "service:b", "B"))
    await store.upsert_relationship(
        GraphRelationship(
            tenant_id=tenant,
            type=RelationshipType.DEPENDS_ON,
            from_key="service:a",
            to_key="service:b",
            source=GraphSource.MANUAL,
        )
    )


async def test_upsert_is_idempotent() -> None:
    store = InMemoryGraphStore()
    await _seed(store)
    await _seed(store)  # second time must converge, not duplicate
    stats = await store.stats("acme")
    assert stats.entities_by_kind == {"service": 2}
    assert stats.relationships_by_type == {"depends_on": 1}


async def test_neighborhood_resolves_endpoints_and_direction() -> None:
    store = InMemoryGraphStore()
    await _seed(store)
    hood = await store.neighborhood("acme", "service:a")
    assert hood is not None
    assert len(hood.neighbors) == 1
    neighbor = hood.neighbors[0]
    assert neighbor.direction == "out"
    assert neighbor.entity.key == "service:b"


async def test_list_relationships_populates_endpoint_names() -> None:
    store = InMemoryGraphStore()
    await _seed(store)
    rels = await store.list_relationships("acme")
    assert rels[0].from_name == "A"
    assert rels[0].to_name == "B"


async def test_tenant_isolation() -> None:
    store = InMemoryGraphStore()
    await _seed(store, "acme")
    assert await store.list_entities("other") == []
    assert await store.neighborhood("other", "service:a") is None
    assert (await store.stats("other")).total_entities == 0
