"""Intelligence engine — fetches bounded inputs and delegates to the analyzers.

Read-only and deterministic (ADR-0020): it composes the knowledge graph (Phase 3) and
the trust layer (Phase 5), so there is nothing to persist or to go stale. Each method
maps to one dashboard; ``overview`` runs all four and returns only the headline metrics.
Inputs are bounded by explicit limits to keep a single request predictable.
"""

from __future__ import annotations

from app.domain.enums import EntityKind, RelationshipType, RiskBand
from app.graph.store import GraphStore
from app.intelligence import debt, dependency, incident, ownership
from app.intelligence.base import (
    DebtReport,
    DependencyReport,
    IncidentReport,
    IntelligenceOverview,
    OwnershipReport,
)
from app.trust.trust_service import TrustService

_REL_LIMIT = 5_000
_ENTITY_LIMIT = 5_000
_CORPUS_LIMIT = 10_000
_ITEM_LIMIT = 100


class IntelligenceService:
    def __init__(self, graph_store: GraphStore, trust_service: TrustService) -> None:
        self._graph = graph_store
        self._trust = trust_service

    async def dependencies(self, tenant_id: str) -> DependencyReport:
        rels = await self._graph.list_relationships(
            tenant_id, RelationshipType.DEPENDS_ON, limit=_REL_LIMIT
        )
        return dependency.analyze_dependencies(rels, node_limit=_ITEM_LIMIT)

    async def debt(self, tenant_id: str) -> DebtReport:
        items = await self._trust.sources(tenant_id, None, _CORPUS_LIMIT, 0)
        return debt.analyze_debt(items, limit=_ITEM_LIMIT)

    async def incidents(self, tenant_id: str) -> IncidentReport:
        incs = await self._graph.list_entities(
            tenant_id, EntityKind.INCIDENT, limit=_ENTITY_LIMIT
        )
        impacts = await self._graph.list_relationships(
            tenant_id, RelationshipType.IMPACTS, limit=_REL_LIMIT
        )
        resolved = await self._graph.list_relationships(
            tenant_id, RelationshipType.RESOLVED, limit=_REL_LIMIT
        )
        return incident.analyze_incidents(incs, impacts, resolved, limit=_ITEM_LIMIT)

    async def ownership(self, tenant_id: str) -> OwnershipReport:
        by_kind = {
            kind: await self._graph.list_entities(
                tenant_id, kind, limit=_ENTITY_LIMIT
            )
            for kind in ownership.TRACKED_KINDS
        }
        owns = await self._graph.list_relationships(
            tenant_id, RelationshipType.OWNS, limit=_REL_LIMIT
        )
        modified = await self._graph.list_relationships(
            tenant_id, RelationshipType.MODIFIED, limit=_REL_LIMIT
        )
        return ownership.analyze_ownership(by_kind, owns, modified, limit=_ITEM_LIMIT)

    async def overview(self, tenant_id: str) -> IntelligenceOverview:
        dep = await self.dependencies(tenant_id)
        deb = await self.debt(tenant_id)
        inc = await self.incidents(tenant_id)
        own = await self.ownership(tenant_id)
        return IntelligenceOverview(
            dependency_high_risk=dep.by_risk.get(RiskBand.HIGH.value, 0),
            dependency_cycles=dep.cycle_count,
            debt_count=deb.debt_count,
            debt_high=deb.by_band.get(RiskBand.HIGH.value, 0),
            incidents_total=inc.total_incidents,
            incidents_unresolved=inc.unresolved_count,
            ownership_coverage=own.overall_coverage,
        )
