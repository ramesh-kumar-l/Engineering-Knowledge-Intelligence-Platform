"""Trust endpoints (api_catalog.md, Phase 5).

Read-only, tenant-scoped trust signals over the ingested corpus:
- ``GET /trust/documents/{id}`` — the full trust profile (Trust Inspector);
- ``GET /trust/sources`` — documents with provenance + trust bands (Source Explorer);
- ``GET /trust/freshness`` — corpus freshness distribution (Freshness Dashboard).

All require VIEWER; trust is computed on read (ADR-0017), so there is nothing to
trigger and no mutation here.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import get_trust_service
from app.core.security import Principal, Role, require_role
from app.domain.enums import SourceType
from app.domain.trust import (
    FreshnessResponse,
    SourceListResponse,
    SourceTrustItem,
    TrustProfileResponse,
)
from app.trust.trust_service import TrustService

router = APIRouter(prefix="/trust", tags=["trust"])


@router.get("/sources", response_model=SourceListResponse)
async def list_sources(
    source_type: SourceType | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    principal: Principal = Depends(require_role(Role.VIEWER)),
    service: TrustService = Depends(get_trust_service),
) -> SourceListResponse:
    items = await service.sources(principal.tenant_id, source_type, limit, offset)
    return SourceListResponse(sources=[SourceTrustItem.from_item(i) for i in items])


@router.get("/freshness", response_model=FreshnessResponse)
async def get_freshness(
    principal: Principal = Depends(require_role(Role.VIEWER)),
    service: TrustService = Depends(get_trust_service),
) -> FreshnessResponse:
    summary = await service.freshness(principal.tenant_id)
    return FreshnessResponse.from_summary(summary)


@router.get("/documents/{document_id}", response_model=TrustProfileResponse)
async def get_document_trust(
    document_id: uuid.UUID,
    principal: Principal = Depends(require_role(Role.VIEWER)),
    service: TrustService = Depends(get_trust_service),
) -> TrustProfileResponse:
    profile = await service.profile(principal.tenant_id, document_id)
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
        )
    return TrustProfileResponse.from_profile(profile)
