"""Knowledge-maintenance agent (Phase 8).

Scans the whole corpus for knowledge debt — stale, unowned and low-confidence
documentation (intelligence Phase 7) plus orphaned components — and produces a
prioritized worklist. Needs no target. Deterministic; no model.
"""

from __future__ import annotations

from app.agents import compose
from app.agents.base import AgentAction, AgentFinding, AgentReport, AgentStepResult
from app.agents.context import AgentContext
from app.domain.enums import AgentStepStatus, AgentType, RiskBand
from app.intelligence.scoring import risk_band

_MAX_DEBT = 8
_MAX_ORPHANS = 8
_LOW_COVERAGE = 0.5


async def run(ctx: AgentContext, target: str) -> AgentReport:
    steps: list[AgentStepResult] = []
    findings: list[AgentFinding] = []
    actions: list[AgentAction] = []

    debt = await ctx.intelligence.debt(ctx.tenant_id)
    top_debt = debt.items[:_MAX_DEBT]
    evidence = compose.evidence_from_debt(top_debt)
    steps.append(
        AgentStepResult(
            name="Scan knowledge debt",
            status=AgentStepStatus.OK if debt.debt_count else AgentStepStatus.EMPTY,
            summary=(
                f"{debt.debt_count} of {debt.total_documents} document(s) carry debt."
                if debt.debt_count
                else "No knowledge debt detected in the corpus."
            ),
            detail={"by_reason": debt.by_reason, "by_band": debt.by_band},
        )
    )
    for reason, count in sorted(debt.by_reason.items()):
        if count:
            findings.append(
                AgentFinding(
                    label=f"Debt — {reason.replace('_', ' ')}",
                    detail=f"{count} document(s) flagged.",
                    severity=_reason_severity(reason),
                )
            )
    for reason, count in sorted(debt.by_reason.items(), reverse=True):
        action = _reason_action(reason, count)
        if action is not None:
            actions.append(action)

    ownership = await ctx.intelligence.ownership(ctx.tenant_id)
    orphans = ownership.orphans[:_MAX_ORPHANS]
    steps.append(
        AgentStepResult(
            name="Check ownership coverage",
            status=AgentStepStatus.OK if ownership.overall_total else AgentStepStatus.EMPTY,
            summary=(
                f"Coverage {ownership.overall_coverage:.0%}; "
                f"{len(ownership.orphans)} orphaned component(s)."
                if ownership.overall_total
                else "No tracked components in the graph yet."
            ),
            detail={"coverage": ownership.overall_coverage, "orphans": len(ownership.orphans)},
        )
    )
    if orphans:
        findings.append(
            AgentFinding(
                label="Orphaned components",
                detail="; ".join(o.name for o in orphans),
                severity=RiskBand.MEDIUM,
                refs=[o.key for o in orphans],
            )
        )
        actions.append(
            AgentAction(
                action="Assign owners to orphaned components.",
                priority=(
                    RiskBand.HIGH
                    if ownership.overall_coverage < _LOW_COVERAGE
                    else RiskBand.MEDIUM
                ),
                rationale=f"Ownership coverage is {ownership.overall_coverage:.0%}.",
            )
        )

    score, band = compose.mean_confidence(evidence)
    headline = (
        f"{debt.debt_count} document(s) with debt; ownership coverage "
        f"{ownership.overall_coverage:.0%}."
    )
    return AgentReport(
        agent_type=AgentType.MAINTENANCE,
        target=None,
        headline=headline,
        confidence=score,
        confidence_band=band,
        findings=findings,
        actions=actions,
        evidence=evidence,
        steps=steps,
    )


def _reason_severity(reason: str) -> RiskBand:
    if reason == "unowned":
        return RiskBand.MEDIUM
    if reason == "stale":
        return RiskBand.MEDIUM
    return RiskBand.LOW


def _reason_action(reason: str, count: int) -> AgentAction | None:
    if not count:
        return None
    if reason == "stale":
        return AgentAction(
            action=f"Refresh {count} stale document(s).",
            priority=risk_band(min(1.0, count / 10)),
            rationale="Stale documentation erodes trust and accelerates drift.",
        )
    if reason == "unowned":
        return AgentAction(
            action=f"Assign owners to {count} unowned document(s).",
            priority=RiskBand.MEDIUM,
            rationale="Unowned knowledge has no one accountable to keep it correct.",
        )
    if reason == "low_confidence":
        return AgentAction(
            action=f"Improve {count} low-confidence document(s).",
            priority=RiskBand.LOW,
            rationale="Process and embed these so they surface reliably in retrieval.",
        )
    return None
