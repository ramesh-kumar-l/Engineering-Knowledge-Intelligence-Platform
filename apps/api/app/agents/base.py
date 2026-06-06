"""Agent value objects (Phase 8).

Frozen, store- and schema-agnostic dataclasses shared by the planners, the service
and the serializer — the same layering the retrieval, graph, trust and intelligence
packages use to keep the engine free of both the ORM and the Pydantic schemas.

An ``AgentReport`` is what a planner returns: a headline + overall confidence, the
``findings`` and recommended ``actions`` it concluded, the trust-carrying ``evidence``
behind them, and the ``steps`` it took (the execution trace). The service persists the
steps as rows and the rest as a JSON snapshot on the run.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any

from app.domain.enums import (
    AgentStepStatus,
    AgentType,
    ConfidenceBand,
    FreshnessBand,
    RiskBand,
    SourceType,
)


@dataclass(frozen=True)
class AgentEvidence:
    """A source backing the agent's findings, carrying its Phase-5 trust."""

    document_id: uuid.UUID
    title: str
    source_type: SourceType
    url: str | None
    snippet: str
    confidence: float
    confidence_band: ConfidenceBand
    freshness_band: FreshnessBand
    age_days: float | None
    owners: list[str]
    ownership_known: bool


@dataclass(frozen=True)
class AgentFinding:
    """A structured insight the agent concluded, optionally severity-ranked."""

    label: str
    detail: str
    severity: RiskBand | None = None
    refs: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class AgentAction:
    """A recommended next action, prioritized so a human can triage the list."""

    action: str
    priority: RiskBand
    rationale: str


@dataclass(frozen=True)
class AgentStepResult:
    """One step in an agent's plan + what it produced (the execution trace)."""

    name: str
    status: AgentStepStatus
    summary: str
    detail: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class AgentReport:
    """A composed, evidence-backed result of one agent run."""

    agent_type: AgentType
    target: str | None
    headline: str
    confidence: float
    confidence_band: ConfidenceBand
    findings: list[AgentFinding] = field(default_factory=list)
    actions: list[AgentAction] = field(default_factory=list)
    evidence: list[AgentEvidence] = field(default_factory=list)
    steps: list[AgentStepResult] = field(default_factory=list)
