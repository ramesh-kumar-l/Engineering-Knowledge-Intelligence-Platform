"""Connector endpoints (api_catalog.md) — catalog, CRUD, and sync trigger.

All routes are RBAC-protected and tenant-scoped via the resolved ``Principal``.
"""

from __future__ import annotations

import uuid

import httpx
from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import (
    get_audit_service,
    get_connector_service,
    get_sync_service,
)
from app.connectors import registry
from app.connectors.catalog import CATALOG
from app.core.security import Principal, Role, require_role
from app.domain.connectors import (
    ConnectorCatalogResponse,
    ConnectorCreate,
    ConnectorListResponse,
    ConnectorOut,
    SourceTypeInfo,
)
from app.domain.sync import SyncRunOut
from app.services.audit_service import AuditService
from app.services.connector_service import ConnectorService, ConnectorValidationError
from app.services.sync_service import SyncService

router = APIRouter(prefix="/connectors", tags=["connectors"])


@router.get("/catalog", response_model=ConnectorCatalogResponse)
async def list_catalog(
    _: Principal = Depends(require_role(Role.VIEWER)),
) -> ConnectorCatalogResponse:
    """List available source types (implemented + planned)."""
    return ConnectorCatalogResponse(
        sources=[SourceTypeInfo.from_spec(spec) for spec in CATALOG]
    )


@router.get("", response_model=ConnectorListResponse)
async def list_connectors(
    principal: Principal = Depends(require_role(Role.VIEWER)),
    service: ConnectorService = Depends(get_connector_service),
) -> ConnectorListResponse:
    connectors = await service.list(principal.tenant_id)
    return ConnectorListResponse(
        connectors=[ConnectorOut.from_model(c) for c in connectors]
    )


@router.post("", response_model=ConnectorOut, status_code=status.HTTP_201_CREATED)
async def create_connector(
    payload: ConnectorCreate,
    principal: Principal = Depends(require_role(Role.EDITOR)),
    service: ConnectorService = Depends(get_connector_service),
    audit: AuditService = Depends(get_audit_service),
) -> ConnectorOut:
    try:
        connector = await service.create(
            tenant_id=principal.tenant_id,
            source_type=payload.source_type,
            name=payload.name,
            config=payload.config,
            secret=payload.secret,
        )
    except ConnectorValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc
    await audit.record(
        tenant_id=principal.tenant_id,
        actor=principal.subject,
        action="connector.create",
        resource_type="connector",
        resource_id=str(connector.id),
        metadata={"source_type": connector.source_type.value},
    )
    return ConnectorOut.from_model(connector)


@router.get("/{connector_id}", response_model=ConnectorOut)
async def get_connector(
    connector_id: uuid.UUID,
    principal: Principal = Depends(require_role(Role.VIEWER)),
    service: ConnectorService = Depends(get_connector_service),
) -> ConnectorOut:
    connector = await service.get(principal.tenant_id, connector_id)
    if connector is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Connector not found")
    return ConnectorOut.from_model(connector)


@router.post("/{connector_id}/sync", response_model=SyncRunOut)
async def trigger_sync(
    connector_id: uuid.UUID,
    principal: Principal = Depends(require_role(Role.EDITOR)),
    service: ConnectorService = Depends(get_connector_service),
    sync_service: SyncService = Depends(get_sync_service),
    audit: AuditService = Depends(get_audit_service),
) -> SyncRunOut:
    connector = await service.get(principal.tenant_id, connector_id)
    if connector is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Connector not found")

    secret = service.decrypt_secret(connector)
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            live = registry.build_connector(
                connector.source_type, connector.config, secret, client
            )
            run = await sync_service.run(connector, live)
    except (registry.ConnectorNotImplemented, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc

    await audit.record(
        tenant_id=principal.tenant_id,
        actor=principal.subject,
        action="connector.sync",
        resource_type="connector",
        resource_id=str(connector.id),
        status=run.status.value,
        metadata={"sync_run_id": str(run.id)},
    )
    return SyncRunOut.from_model(run)
