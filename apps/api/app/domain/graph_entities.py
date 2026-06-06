"""Graph entity/relationship/neighborhood + curation schemas (mirror in contracts)."""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.domain.enums import EntityKind, GraphSource, RelationshipType
from app.graph.base import (
    GraphEntity,
    GraphNeighbor,
    GraphNeighborhood,
    GraphRelationship,
)


class GraphEntityOut(BaseModel):
    kind: EntityKind
    key: str
    name: str
    source: GraphSource
    summary: str | None
    url: str | None
    category: str | None

    @classmethod
    def from_model(cls, e: GraphEntity) -> GraphEntityOut:
        return cls(
            kind=e.kind,
            key=e.key,
            name=e.name,
            source=e.source,
            summary=e.summary,
            url=e.url,
            category=e.category,
        )


class GraphEntityListResponse(BaseModel):
    entities: list[GraphEntityOut]


class GraphRelationshipOut(BaseModel):
    type: RelationshipType
    from_key: str
    from_name: str | None
    from_kind: EntityKind | None
    to_key: str
    to_name: str | None
    to_kind: EntityKind | None

    @classmethod
    def from_model(cls, r: GraphRelationship) -> GraphRelationshipOut:
        return cls(
            type=r.type,
            from_key=r.from_key,
            from_name=r.from_name,
            from_kind=r.from_kind,
            to_key=r.to_key,
            to_name=r.to_name,
            to_kind=r.to_kind,
        )


class GraphRelationshipListResponse(BaseModel):
    relationships: list[GraphRelationshipOut]


class GraphNeighborOut(BaseModel):
    type: RelationshipType
    direction: str
    entity: GraphEntityOut

    @classmethod
    def from_model(cls, n: GraphNeighbor) -> GraphNeighborOut:
        return cls(
            type=n.type,
            direction=n.direction,
            entity=GraphEntityOut.from_model(n.entity),
        )


class GraphNeighborhoodResponse(BaseModel):
    entity: GraphEntityOut
    neighbors: list[GraphNeighborOut]

    @classmethod
    def from_model(cls, hood: GraphNeighborhood) -> GraphNeighborhoodResponse:
        return cls(
            entity=GraphEntityOut.from_model(hood.entity),
            neighbors=[GraphNeighborOut.from_model(n) for n in hood.neighbors],
        )


class EntityCreateRequest(BaseModel):
    kind: EntityKind
    name: str = Field(min_length=1, max_length=512)
    summary: str | None = None
    url: str | None = None


class RelationshipCreateRequest(BaseModel):
    type: RelationshipType
    from_kind: EntityKind
    from_name: str = Field(min_length=1, max_length=512)
    to_kind: EntityKind
    to_name: str = Field(min_length=1, max_length=512)
