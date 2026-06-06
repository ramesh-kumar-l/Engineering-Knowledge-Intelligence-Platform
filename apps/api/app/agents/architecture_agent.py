"""Architecture agent (Phase 8).

Reviews a design area: the decisions on record (trusted sources), the dependency shape
including circular dependencies and high-risk components (intelligence), and stale
documentation risks. Recommends breaking cycles and refreshing aged decisions.
Deterministic; no model.
"""

from __future__ import annotations

from app.agents import compose
from app.agents.base import AgentAction, AgentFinding, AgentReport, AgentStepResult
from app.agents.context import AgentContext
from app.domain.enums import AgentStepStatus, AgentType, FreshnessBand, RiskBand

_EVIDENCE = 6
_MAX_CYCLES = 5
_MAX_RISKY = 5
_STALE = (FreshnessBand.AGING, FreshnessBand.STALE)


async def run(ctx: AgentContext, target: str) -> AgentReport:
    target = (target or "").strip()
    steps: list[AgentStepResult] = []
    findings: list[AgentFinding] = []
    actions: list[AgentAction] = []

    query = f"{target} architecture decision".strip()
    evidence = await compose.gather_evidence(ctx, query, _EVIDENCE)
    steps.append(
        AgentStepResult(
            name="Collect decisions",
            status=AgentStepStatus.OK if evidence else AgentStepStatus.EMPTY,
            summary=(
                f"Found {len(evidence)} decision/architecture source(s)."
                if evidence
                else "No architecture sources found for this area."
            ),
            detail={"query": query, "count": len(evidence)},
        )
    )
    for item in evidence[:3]:
        findings.append(
            AgentFinding(
                label=f"On record: {item.title}",
                detail=item.snippet,
                refs=[str(item.document_id)],
            )
        )

    report = await ctx.intelligence.dependencies(ctx.tenant_id)
    cycles = report.cycles[:_MAX_CYCLES]
    risky = [
        n for n in report.nodes if n.risk_band == RiskBand.HIGH
    ][:_MAX_RISKY]
    steps.append(
        AgentStepResult(
            name="Inspect dependencies",
            status=(
                AgentStepStatus.OK
                if report.total_dependencies
                else AgentStepStatus.EMPTY
            ),
            summary=(
                f"{report.total_dependencies} dependency edge(s), "
                f"{report.cycle_count} cycle(s), {len(risky)} high-risk component(s)."
                if report.total_dependencies
                else "No dependency edges recorded — curate depends_on edges in the graph."
            ),
            detail={"cycles": report.cycle_count, "high_risk": len(risky)},
        )
    )
    for cycle in cycles:
        names = [m.name for m in cycle.members]
        findings.append(
            AgentFinding(
                label="Circular dependency",
                detail=" → ".join(names) + " → " + (names[0] if names else ""),
                severity=RiskBand.HIGH,
                refs=[m.key for m in cycle.members],
            )
        )
        actions.append(
            AgentAction(
                action="Break the circular dependency between " + ", ".join(names) + ".",
                priority=RiskBand.HIGH,
                rationale="Cycles make components impossible to change or deploy independently.",
            )
        )
    if risky:
        findings.append(
            AgentFinding(
                label="High-risk components",
                detail="; ".join(f"{n.name} (risk {n.risk_score:.2f})" for n in risky),
                severity=RiskBand.HIGH,
                refs=[n.key for n in risky],
            )
        )

    stale = [e for e in evidence if e.freshness_band in _STALE]
    steps.append(
        AgentStepResult(
            name="Assess documentation freshness",
            status=AgentStepStatus.OK if stale else AgentStepStatus.EMPTY,
            summary=(
                f"{len(stale)} source(s) are aging or stale."
                if stale
                else "Reviewed sources are reasonably fresh."
            ),
            detail={"stale": len(stale)},
        )
    )
    if stale:
        findings.append(
            AgentFinding(
                label="Stale documentation",
                detail="; ".join(s.title for s in stale),
                severity=RiskBand.MEDIUM,
                refs=[str(s.document_id) for s in stale],
            )
        )
        actions.append(
            AgentAction(
                action="Refresh aged architecture documentation.",
                priority=RiskBand.MEDIUM,
                rationale="Stale decisions mislead readers and accelerate drift.",
            )
        )
    if not evidence:
        actions.append(
            AgentAction(
                action="Record an ADR for this architecture area.",
                priority=RiskBand.MEDIUM,
                rationale="No decision record was found for this area.",
            )
        )

    score, band = compose.mean_confidence(evidence)
    headline = (
        f"Architecture review of '{target or 'the system'}': {report.cycle_count} cycle(s), "
        f"{len(risky)} high-risk component(s), {len(evidence)} source(s)."
    )
    return AgentReport(
        agent_type=AgentType.ARCHITECTURE,
        target=target or None,
        headline=headline,
        confidence=score,
        confidence_band=band,
        findings=findings,
        actions=actions,
        evidence=evidence,
        steps=steps,
    )
