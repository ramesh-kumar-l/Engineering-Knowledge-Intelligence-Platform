"""Graph value objects + key helpers.

Plain, store-agnostic dataclasses passed between the builder, the service, and the
store implementations. A graph node's identity within a tenant is its ``(kind, key)``;
``entity_key`` builds the stable business key for a given kind and natural name.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from app.domain.enums import EntityKind, GraphSource, RelationshipType

_SLUG_RE = re.compile(r"[^a-z0-9]+")


def slugify(value: str) -> str:
    """Lowercase, dash-joined slug used to build stable keys from free text."""
    return _SLUG_RE.sub("-", value.strip().lower()).strip("-") or "unknown"


def entity_key(kind: EntityKind, natural: str) -> str:
    """Stable per-tenant business key, e.g. ``service:checkout-api``.

    ``natural`` is a source identity (a repo path, a login, a document id) that is
    already unique for the kind; it is slugified only for free-text kinds.
    """
    return f"{kind.value}:{natural}"


@dataclass(frozen=True)
class GraphEntity:
    tenant_id: str
    kind: EntityKind
    key: str
    name: str
    source: GraphSource = GraphSource.PROJECTION
    summary: str | None = None
    url: str | None = None
    category: str | None = None


@dataclass(frozen=True)
class GraphRelationship:
    tenant_id: str
    type: RelationshipType
    from_key: str
    to_key: str
    source: GraphSource = GraphSource.PROJECTION
    # Endpoint display metadata (populated on reads; ignored on writes).
    from_kind: EntityKind | None = None
    from_name: str | None = None
    to_kind: EntityKind | None = None
    to_name: str | None = None


@dataclass(frozen=True)
class GraphNeighbor:
    """One edge incident to a focus entity, with the entity on the other end."""

    type: RelationshipType
    direction: str  # "out" (focus -> entity) or "in" (entity -> focus)
    entity: GraphEntity


@dataclass(frozen=True)
class GraphNeighborhood:
    entity: GraphEntity
    neighbors: list[GraphNeighbor] = field(default_factory=list)


@dataclass(frozen=True)
class GraphStats:
    entities_by_kind: dict[str, int] = field(default_factory=dict)
    relationships_by_type: dict[str, int] = field(default_factory=dict)

    @property
    def total_entities(self) -> int:
        return sum(self.entities_by_kind.values())

    @property
    def total_relationships(self) -> int:
        return sum(self.relationships_by_type.values())
