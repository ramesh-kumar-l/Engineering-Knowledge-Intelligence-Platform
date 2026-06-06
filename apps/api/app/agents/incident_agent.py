"""Incident agent (Phase 8).

Triages an incident: pulls related evidence, the incident-impact picture from
intelligence (Phase 7), the most-impacted components and the owners to involve, then
recommends follow-ups for anything unresolved or unowned. Deterministic; no model.
"""

from __future__ import annotations

from app.agents import compose
from app.agents.base import AgentAction, AgentFinding, AgentReport, AgentStepResult
from app.agents.context import AgentContext
from app.domain.enums import AgentStepStatus, AgentType, RiskBand

_EVIDENCE = 6
_MAX_INCIDENTS = 5
_MAX_IMPACTED = 5


async def run(ctx: AgentContext, target: str) -> AgentReport:
    target = (target or "").strip()
    steps: list[AgentStepResult] = []
    findings: list[AgentFinding] = []
    actions: list[AgentAction] = []

    evidence = await compose.gather_evidence(ctx, target, _EVIDENCE)
    steps.append(
        AgentStepResult(
            name="Gather evidence",
            status=AgentStepStatus.OK if evidence else AgentStepStatus.EMPTY,
            summary=(
                f"Found {len(evidence)} related source(s)."
                if evidence
                else "No related sources found in the knowledge base."
            ),
            detail={"query": target, "count": len(evidence)},
        )
    )

    report = await ctx.intelligence.incidents(ctx.tenant_id)
    matched = [i for i in report.incidents if compose.matches(target, i.name, i.key)]
    relevant = (matched or report.incidents)[:_MAX_INCIDENTS]
    unresolved = [i for i in relevant if not i.resolved]
    steps.append(
        AgentStepResult(
            name="Analyze incidents",
            status=AgentStepStatus.OK if relevant else AgentStepStatus.EMPTY,
            summary=(
                f"{len(relevant)} incident(s) in scope, {len(unresolved)} unresolved."
                if relevant
                else "No incidents recorded in the knowledge graph."
            ),
            detail={"matched": len(matched), "unresolved": len(unresolved)},
        )
    )
    for inc in relevant:
        findings.append(
            AgentFinding(
                label=f"Incident: {inc.name}",
                detail=(
                    ("Unresolved" if not inc.resolved else "Resolved")
                    + f"; impacts {inc.impacted_count} component(s)."
                ),
                severity=RiskBand.HIGH if not inc.resolved else RiskBand.LOW,
                refs=[m.name for m in inc.impacted],
            )
        )
        if not inc.resolved:
            actions.append(
                AgentAction(
                    action=f"Follow up on unresolved incident '{inc.name}'.",
                    priority=RiskBand.HIGH,
                    rationale="No resolution is recorded in the knowledge graph.",
                )
            )

    top = report.impacted_components[:_MAX_IMPACTED]
    if top:
        findings.append(
            AgentFinding(
                label="Most-impacted components",
                detail="; ".join(f"{c.name} ({c.incident_count})" for c in top),
                severity=RiskBand.MEDIUM,
                refs=[c.key for c in top],
            )
        )

    owner_names: list[str] = []
    for component in top:
        owner_names.extend(await compose.owners_of(ctx, component.key))
    owner_names = list(dict.fromkeys(owner_names))
    steps.append(
        AgentStepResult(
            name="Identify owners",
            status=AgentStepStatus.OK if owner_names else AgentStepStatus.EMPTY,
            summary=(
                "Owners to involve: " + ", ".join(owner_names)
                if owner_names
                else "No owners recorded for the impacted components."
            ),
            detail={"owners": owner_names},
        )
    )
    if owner_names:
        findings.append(
            AgentFinding(label="Owners to involve", detail=", ".join(owner_names))
        )
    elif top:
        actions.append(
            AgentAction(
                action="Assign owners to the most-impacted components.",
                priority=RiskBand.MEDIUM,
                rationale="No owners are recorded for components hit by incidents.",
            )
        )

    if not evidence:
        actions.append(
            AgentAction(
                action="Document this incident and its resolution.",
                priority=RiskBand.MEDIUM,
                rationale="Little written evidence was found for this incident.",
            )
        )

    score, band = compose.mean_confidence(evidence)
    headline = (
        f"{len(unresolved)} unresolved of {len(relevant)} incident(s) in scope; "
        f"{len(evidence)} source(s) reviewed."
        if relevant
        else "No incidents are recorded yet — build the graph and ingest incident sources."
    )
    return AgentReport(
        agent_type=AgentType.INCIDENT,
        target=target or None,
        headline=headline,
        confidence=score,
        confidence_band=band,
        findings=findings,
        actions=actions,
        evidence=evidence,
        steps=steps,
    )
