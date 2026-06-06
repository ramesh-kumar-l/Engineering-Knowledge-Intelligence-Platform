"""Engineering Intelligence API schemas (mirrored in packages/contracts, Phase 7)."""

from __future__ import annotations

import uuid

from pydantic import BaseModel

from app.domain.enums import (
    ConfidenceBand,
    EntityKind,
    FreshnessBand,
    RiskBand,
    SourceType,
)
from app.intelligence.base import (
    DebtItem,
    DebtReport,
    DependencyNode,
    DependencyReport,
    ImpactedComponent,
    IncidentReport,
    IntelligenceOverview,
    NodeRef,
    OwnerLoad,
    OwnershipCoverage,
    OwnershipReport,
)


class NodeRefOut(BaseModel):
    key: str
    name: str
    kind: EntityKind

    @classmethod
    def of(cls, ref: NodeRef) -> NodeRefOut:
        return cls(key=ref.key, name=ref.name, kind=ref.kind)


# --- Dependencies -------------------------------------------------------------


class DependencyNodeOut(BaseModel):
    key: str
    name: str
    kind: EntityKind
    fan_in: int
    fan_out: int
    in_cycle: bool
    risk_score: float
    risk_band: RiskBand


class DependencyCycleOut(BaseModel):
    members: list[NodeRefOut]


class DependencyReportResponse(BaseModel):
    total_nodes: int
    total_dependencies: int
    cycle_count: int
    by_risk: dict[str, int]
    nodes: list[DependencyNodeOut]
    cycles: list[DependencyCycleOut]

    @classmethod
    def of(cls, report: DependencyReport) -> DependencyReportResponse:
        return cls(
            total_nodes=report.total_nodes,
            total_dependencies=report.total_dependencies,
            cycle_count=report.cycle_count,
            by_risk=report.by_risk,
            nodes=[_node(n) for n in report.nodes],
            cycles=[
                DependencyCycleOut(members=[NodeRefOut.of(m) for m in c.members])
                for c in report.cycles
            ],
        )


def _node(n: DependencyNode) -> DependencyNodeOut:
    return DependencyNodeOut(
        key=n.key,
        name=n.name,
        kind=n.kind,
        fan_in=n.fan_in,
        fan_out=n.fan_out,
        in_cycle=n.in_cycle,
        risk_score=n.risk_score,
        risk_band=n.risk_band,
    )


# --- Technical debt -----------------------------------------------------------


class DebtItemOut(BaseModel):
    document_id: uuid.UUID
    title: str
    source_type: SourceType
    url: str | None
    confidence: float
    confidence_band: ConfidenceBand
    freshness_band: FreshnessBand
    age_days: float | None
    has_owner: bool
    severity_score: float
    severity_band: RiskBand
    reasons: list[str]


class DebtReportResponse(BaseModel):
    total_documents: int
    debt_count: int
    by_reason: dict[str, int]
    by_band: dict[str, int]
    items: list[DebtItemOut]

    @classmethod
    def of(cls, report: DebtReport) -> DebtReportResponse:
        return cls(
            total_documents=report.total_documents,
            debt_count=report.debt_count,
            by_reason=report.by_reason,
            by_band=report.by_band,
            items=[_debt(i) for i in report.items],
        )


def _debt(i: DebtItem) -> DebtItemOut:
    return DebtItemOut(
        document_id=i.document_id,
        title=i.title,
        source_type=i.source_type,
        url=i.url,
        confidence=i.confidence,
        confidence_band=i.confidence_band,
        freshness_band=i.freshness_band,
        age_days=i.age_days,
        has_owner=i.has_owner,
        severity_score=i.severity_score,
        severity_band=i.severity_band,
        reasons=i.reasons,
    )


# --- Incidents ----------------------------------------------------------------


class IncidentInsightOut(BaseModel):
    key: str
    name: str
    url: str | None
    resolved: bool
    impacted_count: int
    impacted: list[NodeRefOut]


class ImpactedComponentOut(BaseModel):
    key: str
    name: str
    kind: EntityKind
    incident_count: int


class IncidentReportResponse(BaseModel):
    total_incidents: int
    resolved_count: int
    unresolved_count: int
    incidents: list[IncidentInsightOut]
    impacted_components: list[ImpactedComponentOut]

    @classmethod
    def of(cls, report: IncidentReport) -> IncidentReportResponse:
        return cls(
            total_incidents=report.total_incidents,
            resolved_count=report.resolved_count,
            unresolved_count=report.unresolved_count,
            incidents=[
                IncidentInsightOut(
                    key=i.key,
                    name=i.name,
                    url=i.url,
                    resolved=i.resolved,
                    impacted_count=i.impacted_count,
                    impacted=[NodeRefOut.of(m) for m in i.impacted],
                )
                for i in report.incidents
            ],
            impacted_components=[_component(c) for c in report.impacted_components],
        )


def _component(c: ImpactedComponent) -> ImpactedComponentOut:
    return ImpactedComponentOut(
        key=c.key, name=c.name, kind=c.kind, incident_count=c.incident_count
    )


# --- Ownership ----------------------------------------------------------------


class OwnershipCoverageOut(BaseModel):
    kind: EntityKind
    total: int
    owned: int
    unowned: int
    coverage: float


class OwnerLoadOut(BaseModel):
    key: str
    name: str
    kind: EntityKind
    owned_count: int


class OwnershipReportResponse(BaseModel):
    overall_total: int
    overall_owned: int
    overall_coverage: float
    coverages: list[OwnershipCoverageOut]
    orphans: list[NodeRefOut]
    top_owners: list[OwnerLoadOut]

    @classmethod
    def of(cls, report: OwnershipReport) -> OwnershipReportResponse:
        return cls(
            overall_total=report.overall_total,
            overall_owned=report.overall_owned,
            overall_coverage=report.overall_coverage,
            coverages=[_coverage(c) for c in report.coverages],
            orphans=[NodeRefOut.of(o) for o in report.orphans],
            top_owners=[_owner(o) for o in report.top_owners],
        )


def _coverage(c: OwnershipCoverage) -> OwnershipCoverageOut:
    return OwnershipCoverageOut(
        kind=c.kind,
        total=c.total,
        owned=c.owned,
        unowned=c.unowned,
        coverage=c.coverage,
    )


def _owner(o: OwnerLoad) -> OwnerLoadOut:
    return OwnerLoadOut(key=o.key, name=o.name, kind=o.kind, owned_count=o.owned_count)


# --- Overview -----------------------------------------------------------------


class OverviewResponse(BaseModel):
    dependency_high_risk: int
    dependency_cycles: int
    debt_count: int
    debt_high: int
    incidents_total: int
    incidents_unresolved: int
    ownership_coverage: float

    @classmethod
    def of(cls, overview: IntelligenceOverview) -> OverviewResponse:
        return cls(
            dependency_high_risk=overview.dependency_high_risk,
            dependency_cycles=overview.dependency_cycles,
            debt_count=overview.debt_count,
            debt_high=overview.debt_high,
            incidents_total=overview.incidents_total,
            incidents_unresolved=overview.incidents_unresolved,
            ownership_coverage=overview.ownership_coverage,
        )
