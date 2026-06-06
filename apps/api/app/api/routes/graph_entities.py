"""Knowledge-graph entity/relationship endpoints (api_catalog.md, Phase 3).

Read routes (viewer) power the Knowledge/Service/Team explorers and the Dependency
Graph. Write routes (editor) let architects curate Services and ``depends_on`` edges
the projection cannot derive; each write records an audit event. Tenant-scoped.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import get_audit_service, get_graph_service
from app.core.security import Principal, Role, require_role
from app.domain.enums import EntityKind, RelationshipType
from app.domain.graph_entities import (
    EntityCreateRequest,
    GraphEntityListResponse,
    GraphEntityOut,
    GraphNeighborhoodResponse,
    GraphRelationshipListResponse,
    GraphRelationshipOut,
    RelationshipCreateRequest,
)
from app.services.audit_service import AuditService
from app.services.graph_service import GraphService

router = APIRouter(prefix="/graph", tags=["graph"])


@router.get("/entities", response_model=GraphEntityListResponse)
async def list_entities(
    kind: EntityKind | None = Query(default=None),
    search: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    principal: Principal = Depends(require_role(Role.VIEWER)),
    service: GraphService = Depends(get_graph_service),
) -> GraphEntityListResponse:
    entities = await service.list_entities(
        principal.tenant_id, kind, search, limit, offset
    )
    return GraphEntityListResponse(
        entities=[GraphEntityOut.from_model(e) for e in entities]
    )


@router.get("/entity", response_model=GraphNeighborhoodResponse)
async def get_entity(
    key: str = Query(min_length=1),
    principal: Principal = Depends(require_role(Role.VIEWER)),
    service: GraphService = Depends(get_graph_service),
) -> GraphNeighborhoodResponse:
    hood = await service.neighborhood(principal.tenant_id, key)
    if hood is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Entity not found"
        )
    return GraphNeighborhoodResponse.from_model(hood)


@router.get("/relationships", response_model=GraphRelationshipListResponse)
async def list_relationships(
    type: RelationshipType | None = Query(default=None),
    limit: int = Query(default=200, ge=1, le=1000),
    principal: Principal = Depends(require_role(Role.VIEWER)),
    service: GraphService = Depends(get_graph_service),
) -> GraphRelationshipListResponse:
    rels = await service.list_relationships(principal.tenant_id, type, limit)
    return GraphRelationshipListResponse(
        relationships=[GraphRelationshipOut.from_model(r) for r in rels]
    )


@router.post("/entities", response_model=GraphEntityOut)
async def create_entity(
    payload: EntityCreateRequest,
    principal: Principal = Depends(require_role(Role.EDITOR)),
    service: GraphService = Depends(get_graph_service),
    audit: AuditService = Depends(get_audit_service),
) -> GraphEntityOut:
    entity = await service.create_entity(
        principal.tenant_id, payload.kind, payload.name, payload.summary, payload.url
    )
    await audit.record(
        tenant_id=principal.tenant_id,
        actor=principal.subject,
        action="graph.entity.create",
        resource_type="graph_entity",
        resource_id=entity.key,
        status="created",
        metadata={"kind": entity.kind.value},
    )
    return GraphEntityOut.from_model(entity)


@router.post("/relationships", response_model=GraphRelationshipOut)
async def create_relationship(
    payload: RelationshipCreateRequest,
    principal: Principal = Depends(require_role(Role.EDITOR)),
    service: GraphService = Depends(get_graph_service),
    audit: AuditService = Depends(get_audit_service),
) -> GraphRelationshipOut:
    rel = await service.create_relationship(
        principal.tenant_id,
        payload.type,
        payload.from_kind,
        payload.from_name,
        payload.to_kind,
        payload.to_name,
    )
    await audit.record(
        tenant_id=principal.tenant_id,
        actor=principal.subject,
        action="graph.relationship.create",
        resource_type="graph_relationship",
        resource_id=f"{rel.from_key}->{rel.to_key}",
        status="created",
        metadata={"type": rel.type.value},
    )
    return GraphRelationshipOut.from_model(rel)
