"""Intelligence primitives shared by the analyzers, service and API layer (Phase 7).

Frozen, store-agnostic dataclasses — the same layering ``app/trust/base.py`` and
``app/graph/base.py`` use to keep the analyzers free of both the ORM and the Pydantic
schemas. ``kind_of`` recovers an entity kind from a graph key (``"service:checkout"``)
so reports stay correct even when a store omits edge-endpoint metadata.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field

from app.domain.enums import (
    ConfidenceBand,
    EntityKind,
    FreshnessBand,
    RiskBand,
    SourceType,
)


def kind_of(key: str) -> EntityKind:
    """Best-effort entity kind from a graph key like ``"service:checkout"``."""
    prefix = key.split(":", 1)[0]
    try:
        return EntityKind(prefix)
    except ValueError:
        return EntityKind.DOCUMENT


@dataclass(frozen=True)
class NodeRef:
    """A lightweight reference to a graph entity (key + display + kind)."""

    key: str
    name: str
    kind: EntityKind


# --- Dependency intelligence ---------------------------------------------------


@dataclass(frozen=True)
class DependencyNode:
    """A component in the dependency graph with its risk profile."""

    key: str
    name: str
    kind: EntityKind
    fan_in: int  # how many components depend on this one (blast radius)
    fan_out: int  # how many components this one depends on
    in_cycle: bool
    risk_score: float
    risk_band: RiskBand


@dataclass(frozen=True)
class DependencyCycle:
    """A circular dependency — every member transitively depends on itself."""

    members: list[NodeRef] = field(default_factory=list)


@dataclass(frozen=True)
class DependencyReport:
    total_nodes: int
    total_dependencies: int
    cycle_count: int
    by_risk: dict[str, int]
    nodes: list[DependencyNode] = field(default_factory=list)
    cycles: list[DependencyCycle] = field(default_factory=list)


# --- Technical-debt intelligence ----------------------------------------------


@dataclass(frozen=True)
class DebtItem:
    """A document carrying technical debt, with the reasons it was flagged."""

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
    reasons: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class DebtReport:
    total_documents: int
    debt_count: int
    by_reason: dict[str, int]
    by_band: dict[str, int]
    items: list[DebtItem] = field(default_factory=list)


# --- Incident intelligence ----------------------------------------------------


@dataclass(frozen=True)
class IncidentInsight:
    key: str
    name: str
    url: str | None
    resolved: bool
    impacted_count: int
    impacted: list[NodeRef] = field(default_factory=list)


@dataclass(frozen=True)
class ImpactedComponent:
    """A component ranked by how many incidents have impacted it."""

    key: str
    name: str
    kind: EntityKind
    incident_count: int


@dataclass(frozen=True)
class IncidentReport:
    total_incidents: int
    resolved_count: int
    unresolved_count: int
    incidents: list[IncidentInsight] = field(default_factory=list)
    impacted_components: list[ImpactedComponent] = field(default_factory=list)


# --- Ownership intelligence ---------------------------------------------------


@dataclass(frozen=True)
class OwnershipCoverage:
    kind: EntityKind
    total: int
    owned: int
    unowned: int
    coverage: float


@dataclass(frozen=True)
class OwnerLoad:
    """How many tracked components a single owner is accountable for (key-person risk)."""

    key: str
    name: str
    kind: EntityKind
    owned_count: int


@dataclass(frozen=True)
class OwnershipReport:
    overall_total: int
    overall_owned: int
    overall_coverage: float
    coverages: list[OwnershipCoverage] = field(default_factory=list)
    orphans: list[NodeRef] = field(default_factory=list)
    top_owners: list[OwnerLoad] = field(default_factory=list)


# --- Overview -----------------------------------------------------------------


@dataclass(frozen=True)
class IntelligenceOverview:
    """Headline metrics for the Intelligence Dashboard, one number per concern."""

    dependency_high_risk: int
    dependency_cycles: int
    debt_count: int
    debt_high: int
    incidents_total: int
    incidents_unresolved: int
    ownership_coverage: float
