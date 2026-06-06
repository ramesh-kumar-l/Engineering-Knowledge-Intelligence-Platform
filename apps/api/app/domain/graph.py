"""Graph build-run + stats API schemas (mirrored in packages/contracts)."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.domain.enums import SyncEventLevel, SyncStatus
from app.graph.base import GraphStats
from app.models.graph import GraphBuildEvent, GraphBuildRun


class GraphBuildTriggerRequest(BaseModel):
    """Optional scope for a graph build. Empty body projects the whole tenant."""

    limit: int = Field(default=1000, ge=1, le=10000)


class GraphBuildRunOut(BaseModel):
    id: uuid.UUID
    status: SyncStatus
    documents_seen: int
    entity_count: int
    relationship_count: int
    error: str | None
    started_at: datetime
    finished_at: datetime | None

    @classmethod
    def from_model(cls, model: GraphBuildRun) -> GraphBuildRunOut:
        return cls(
            id=model.id,
            status=model.status,
            documents_seen=model.documents_seen,
            entity_count=model.entity_count,
            relationship_count=model.relationship_count,
            error=model.error,
            started_at=model.started_at,
            finished_at=model.finished_at,
        )


class GraphBuildRunListResponse(BaseModel):
    runs: list[GraphBuildRunOut]


class GraphBuildEventOut(BaseModel):
    id: uuid.UUID
    level: SyncEventLevel
    message: str
    created_at: datetime

    @classmethod
    def from_model(cls, model: GraphBuildEvent) -> GraphBuildEventOut:
        return cls(
            id=model.id,
            level=model.level,
            message=model.message,
            created_at=model.created_at,
        )


class GraphBuildEventListResponse(BaseModel):
    events: list[GraphBuildEventOut]


class GraphStatsResponse(BaseModel):
    """Aggregate graph size for the Knowledge Explorer header."""

    total_entities: int
    total_relationships: int
    entities_by_kind: dict[str, int]
    relationships_by_type: dict[str, int]

    @classmethod
    def from_stats(cls, stats: GraphStats) -> GraphStatsResponse:
        return cls(
            total_entities=stats.total_entities,
            total_relationships=stats.total_relationships,
            entities_by_kind=stats.entities_by_kind,
            relationships_by_type=stats.relationships_by_type,
        )
