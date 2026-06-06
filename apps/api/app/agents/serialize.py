"""JSON serialization of an AgentReport's conclusions for run persistence (Phase 8).

Keeps the service free of Pydantic: the report's headline, confidence, findings,
actions and evidence are stored as a JSON snapshot on the run (the execution ``steps``
are persisted as their own rows). The produced shape matches
``app/domain/agents.ResultBody`` exactly, so the route validates it directly on read.
Enum-typed fields are stringified (``str()`` yields the wire value for real ``StrEnum``
members and for ``source_type`` arriving from the DB as a plain string).
"""

from __future__ import annotations

from typing import Any

from app.agents.base import AgentAction, AgentEvidence, AgentFinding, AgentReport


def result_to_dict(report: AgentReport) -> dict[str, Any]:
    return {
        "headline": report.headline,
        "confidence": report.confidence,
        "confidence_band": str(report.confidence_band),
        "findings": [_finding(f) for f in report.findings],
        "actions": [_action(a) for a in report.actions],
        "evidence": [_evidence(e) for e in report.evidence],
    }


def _finding(f: AgentFinding) -> dict[str, Any]:
    return {
        "label": f.label,
        "detail": f.detail,
        "severity": str(f.severity) if f.severity is not None else None,
        "refs": list(f.refs),
    }


def _action(a: AgentAction) -> dict[str, Any]:
    return {
        "action": a.action,
        "priority": str(a.priority),
        "rationale": a.rationale,
    }


def _evidence(e: AgentEvidence) -> dict[str, Any]:
    return {
        "document_id": str(e.document_id),
        "title": e.title,
        "source_type": str(e.source_type),
        "url": e.url,
        "snippet": e.snippet,
        "confidence": e.confidence,
        "confidence_band": str(e.confidence_band),
        "freshness_band": str(e.freshness_band),
        "age_days": e.age_days,
        "owners": list(e.owners),
        "ownership_known": e.ownership_known,
    }
