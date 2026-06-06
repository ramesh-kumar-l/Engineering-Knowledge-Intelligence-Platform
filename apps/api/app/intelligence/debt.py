"""Technical-debt intelligence — severity over the trust read model (Phase 7).

Pure and deterministic: takes the Phase-5 ``SourceItem`` list (confidence/freshness/
ownership already computed) and flags documents that are *low-confidence*, *stale* or
*unowned*. Severity blends those three signals; the report aggregates by reason and by
band so the dashboard can lead with the worst debt first. A document with none of the
reasons is not debt and is excluded from the items list (but still counted in the total).
"""

from __future__ import annotations

from app.domain.enums import ConfidenceBand, FreshnessBand, RiskBand
from app.intelligence import scoring
from app.intelligence.base import DebtItem, DebtReport
from app.trust.base import SourceItem

_REASON_LOW_CONFIDENCE = "low_confidence"
_REASON_STALE = "stale"
_REASON_UNOWNED = "unowned"

# Per-band freshness penalty feeding the severity blend (ADR-0020 heuristic).
_FRESHNESS_PENALTY = {
    FreshnessBand.STALE: 1.0,
    FreshnessBand.AGING: 0.6,
    FreshnessBand.RECENT: 0.25,
    FreshnessBand.FRESH: 0.0,
}
_W_CONFIDENCE = 0.5
_W_FRESHNESS = 0.3
_W_OWNERSHIP = 0.2


def analyze_debt(items: list[SourceItem], limit: int = 100) -> DebtReport:
    debt_items: list[DebtItem] = []
    by_reason: dict[str, int] = {
        _REASON_LOW_CONFIDENCE: 0,
        _REASON_STALE: 0,
        _REASON_UNOWNED: 0,
    }
    by_band: dict[str, int] = dict.fromkeys((b.value for b in RiskBand), 0)

    for item in items:
        reasons = _reasons(item)
        if not reasons:
            continue
        for reason in reasons:
            by_reason[reason] += 1
        debt_item = _item(item, reasons)
        by_band[debt_item.severity_band.value] += 1
        debt_items.append(debt_item)

    debt_items.sort(key=lambda d: (-d.severity_score, d.title.lower()))
    return DebtReport(
        total_documents=len(items),
        debt_count=len(debt_items),
        by_reason=by_reason,
        by_band=by_band,
        items=debt_items[:limit],
    )


def _reasons(item: SourceItem) -> list[str]:
    reasons: list[str] = []
    if item.confidence_band == ConfidenceBand.LOW:
        reasons.append(_REASON_LOW_CONFIDENCE)
    if item.freshness_band in (FreshnessBand.AGING, FreshnessBand.STALE):
        reasons.append(_REASON_STALE)
    if not item.has_owner:
        reasons.append(_REASON_UNOWNED)
    return reasons


def _item(item: SourceItem, reasons: list[str]) -> DebtItem:
    severity = scoring.clamp(
        _W_CONFIDENCE * (1.0 - item.confidence)
        + _W_FRESHNESS * _FRESHNESS_PENALTY[item.freshness_band]
        + _W_OWNERSHIP * (0.0 if item.has_owner else 1.0)
    )
    return DebtItem(
        document_id=item.document_id,
        title=item.title,
        source_type=item.source_type,
        url=item.url,
        confidence=item.confidence,
        confidence_band=item.confidence_band,
        freshness_band=item.freshness_band,
        age_days=item.age_days,
        has_owner=item.has_owner,
        severity_score=round(severity, 4),
        severity_band=scoring.risk_band(severity),
        reasons=reasons,
    )
