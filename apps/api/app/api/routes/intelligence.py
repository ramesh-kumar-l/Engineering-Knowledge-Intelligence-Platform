"""Engineering Intelligence endpoints (api_catalog.md, Phase 7).

Read-only, tenant-scoped intelligence composed over the knowledge graph + trust:
- ``GET /intelligence/overview`` — headline metrics (Intelligence Dashboard);
- ``GET /intelligence/dependencies`` — risk + cycles (Dependency Risk Dashboard);
- ``GET /intelligence/debt`` — technical-debt severity (Technical Debt Dashboard);
- ``GET /intelligence/incidents`` — incident impact + resolution;
- ``GET /intelligence/ownership`` — ownership coverage + orphans + key-person risk.

All require VIEWER; everything is computed on read (ADR-0020), so there is nothing to
trigger and no mutation here.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import get_intelligence_service
from app.core.security import Principal, Role, require_role
from app.domain.intelligence import (
    DebtReportResponse,
    DependencyReportResponse,
    IncidentReportResponse,
    OverviewResponse,
    OwnershipReportResponse,
)
from app.intelligence.intelligence_service import IntelligenceService

router = APIRouter(prefix="/intelligence", tags=["intelligence"])


@router.get("/overview", response_model=OverviewResponse)
async def get_overview(
    principal: Principal = Depends(require_role(Role.VIEWER)),
    service: IntelligenceService = Depends(get_intelligence_service),
) -> OverviewResponse:
    return OverviewResponse.of(await service.overview(principal.tenant_id))


@router.get("/dependencies", response_model=DependencyReportResponse)
async def get_dependencies(
    principal: Principal = Depends(require_role(Role.VIEWER)),
    service: IntelligenceService = Depends(get_intelligence_service),
) -> DependencyReportResponse:
    return DependencyReportResponse.of(await service.dependencies(principal.tenant_id))


@router.get("/debt", response_model=DebtReportResponse)
async def get_debt(
    principal: Principal = Depends(require_role(Role.VIEWER)),
    service: IntelligenceService = Depends(get_intelligence_service),
) -> DebtReportResponse:
    return DebtReportResponse.of(await service.debt(principal.tenant_id))


@router.get("/incidents", response_model=IncidentReportResponse)
async def get_incidents(
    principal: Principal = Depends(require_role(Role.VIEWER)),
    service: IntelligenceService = Depends(get_intelligence_service),
) -> IncidentReportResponse:
    return IncidentReportResponse.of(await service.incidents(principal.tenant_id))


@router.get("/ownership", response_model=OwnershipReportResponse)
async def get_ownership(
    principal: Principal = Depends(require_role(Role.VIEWER)),
    service: IntelligenceService = Depends(get_intelligence_service),
) -> OwnershipReportResponse:
    return OwnershipReportResponse.of(await service.ownership(principal.tenant_id))
