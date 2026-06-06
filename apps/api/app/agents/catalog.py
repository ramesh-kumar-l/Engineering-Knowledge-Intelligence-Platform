"""The agent catalog — what agents exist and how to launch them (Phase 8).

Drives the Agent Workspace launcher. ``needs_target`` tells the UI whether to require a
focus (a service/component/incident); the maintenance agent scans the whole corpus and
needs none.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.domain.enums import AgentType


@dataclass(frozen=True)
class AgentInfo:
    type: AgentType
    label: str
    description: str
    needs_target: bool
    target_hint: str


_CATALOG: tuple[AgentInfo, ...] = (
    AgentInfo(
        type=AgentType.INCIDENT,
        label="Incident Agent",
        description=(
            "Triage an incident: who/what it impacts, whether it is resolved, the "
            "components most often hit, and the evidence and owners to involve."
        ),
        needs_target=True,
        target_hint="An incident, service or symptom (e.g. 'checkout outage')",
    ),
    AgentInfo(
        type=AgentType.ONBOARDING,
        label="Onboarding Agent",
        description=(
            "Ramp onto a component: what it is, who owns it, what it depends on, and "
            "the most trustworthy sources to read first."
        ),
        needs_target=True,
        target_hint="A service, repository or team (e.g. 'billing service')",
    ),
    AgentInfo(
        type=AgentType.ARCHITECTURE,
        label="Architecture Agent",
        description=(
            "Review a design: the decisions on record, the dependency shape, circular "
            "dependencies and high-risk components, plus stale documentation risks."
        ),
        needs_target=True,
        target_hint="An architecture area or service (e.g. 'payments architecture')",
    ),
    AgentInfo(
        type=AgentType.MAINTENANCE,
        label="Knowledge Maintenance Agent",
        description=(
            "Surface knowledge debt across the corpus: stale, unowned and low-confidence "
            "documentation, plus orphaned components, as a prioritized worklist."
        ),
        needs_target=False,
        target_hint="",
    ),
)

_BY_TYPE = {info.type: info for info in _CATALOG}


def catalog() -> tuple[AgentInfo, ...]:
    return _CATALOG


def info_for(agent_type: AgentType) -> AgentInfo:
    return _BY_TYPE[agent_type]
