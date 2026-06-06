"""Onboarding agent (Phase 8).

Helps an engineer ramp onto a component: what it is (trusted sources), who owns it
(graph), and what it depends on plus its dependency risk (intelligence). Recommends a
reading order and who to contact. Deterministic; no model.
"""

from __future__ import annotations

from app.agents import compose
from app.agents.base import AgentAction, AgentFinding, AgentReport, AgentStepResult
from app.agents.context import AgentContext
from app.domain.enums import AgentStepStatus, AgentType, RiskBand
from app.intelligence.base import DependencyNode

_EVIDENCE = 6
_ENTITY_SCAN = 25


async def run(ctx: AgentContext, target: str) -> AgentReport:
    target = (target or "").strip()
    steps: list[AgentStepResult] = []
    findings: list[AgentFinding] = []
    actions: list[AgentAction] = []

    if not target:
        return _no_target(steps)

    evidence = await compose.gather_evidence(ctx, target, _EVIDENCE)
    steps.append(
        AgentStepResult(
            name="Gather sources",
            status=AgentStepStatus.OK if evidence else AgentStepStatus.EMPTY,
            summary=(
                f"Found {len(evidence)} source(s) to read first."
                if evidence
                else "No sources found — try ingesting and indexing more documentation."
            ),
            detail={"query": target, "count": len(evidence)},
        )
    )
    for item in evidence[:3]:
        findings.append(
            AgentFinding(
                label=f"Read: {item.title}",
                detail=item.snippet,
                refs=[str(item.document_id)],
            )
        )

    owners = await _owners(ctx, target)
    owners = owners or list(dict.fromkeys(o for e in evidence for o in e.owners))
    steps.append(
        AgentStepResult(
            name="Find owners",
            status=AgentStepStatus.OK if owners else AgentStepStatus.EMPTY,
            summary=(
                "Owners/contacts: " + ", ".join(owners)
                if owners
                else "Ownership is unknown for this component."
            ),
            detail={"owners": owners},
        )
    )
    if owners:
        findings.append(AgentFinding(label="Owners to contact", detail=", ".join(owners)))
        actions.append(
            AgentAction(
                action=f"Introduce yourself to {owners[0]} for a walkthrough.",
                priority=RiskBand.LOW,
                rationale="They are recorded as accountable for this component.",
            )
        )
    else:
        actions.append(
            AgentAction(
                action="Identify and record an owner for this component.",
                priority=RiskBand.MEDIUM,
                rationale="Onboarding is slower when ownership is unknown.",
            )
        )

    node = await _dependency_node(ctx, target)
    steps.append(
        AgentStepResult(
            name="Map dependencies",
            status=AgentStepStatus.OK if node else AgentStepStatus.EMPTY,
            summary=(
                f"Depends on {node.fan_out}, depended on by {node.fan_in}; "
                f"risk {node.risk_band.value}."
                if node
                else "No dependency edges recorded for this component."
            ),
            detail={"matched": node.key if node else None},
        )
    )
    if node:
        findings.append(
            AgentFinding(
                label="Dependency profile",
                detail=(
                    f"Fan-in {node.fan_in}, fan-out {node.fan_out}"
                    + (", in a dependency cycle" if node.in_cycle else "")
                    + f"; risk {node.risk_band.value}."
                ),
                severity=node.risk_band,
                refs=[node.key],
            )
        )
        if node.risk_band == RiskBand.HIGH:
            actions.append(
                AgentAction(
                    action=f"Review the dependencies of '{node.name}' carefully.",
                    priority=RiskBand.HIGH,
                    rationale="It is a high-risk component (large blast radius or in a cycle).",
                )
            )

    score, band = compose.mean_confidence(evidence)
    headline = (
        f"Onboarding brief for '{target}': {len(evidence)} source(s), "
        f"{len(owners)} owner(s)."
    )
    return AgentReport(
        agent_type=AgentType.ONBOARDING,
        target=target,
        headline=headline,
        confidence=score,
        confidence_band=band,
        findings=findings,
        actions=actions,
        evidence=evidence,
        steps=steps,
    )


async def _owners(ctx: AgentContext, target: str) -> list[str]:
    entities = await ctx.graph.list_entities(
        ctx.tenant_id, None, search=target, limit=_ENTITY_SCAN
    )
    for entity in entities:
        owners = await compose.owners_of(ctx, entity.key)
        if owners:
            return owners
    return []


async def _dependency_node(ctx: AgentContext, target: str) -> DependencyNode | None:
    report = await ctx.intelligence.dependencies(ctx.tenant_id)
    for node in report.nodes:
        if compose.matches(target, node.name, node.key):
            return node
    return None


def _no_target(steps: list[AgentStepResult]) -> AgentReport:
    steps.append(
        AgentStepResult(
            name="Validate input",
            status=AgentStepStatus.EMPTY,
            summary="No component was provided to onboard onto.",
            detail={},
        )
    )
    return AgentReport(
        agent_type=AgentType.ONBOARDING,
        target=None,
        headline="Provide a service, repository or team to onboard onto.",
        confidence=0.0,
        confidence_band=compose.mean_confidence([])[1],
        steps=steps,
    )
