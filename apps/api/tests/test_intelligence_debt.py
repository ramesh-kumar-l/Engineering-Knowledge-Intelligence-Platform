"""Pure technical-debt analyzer — reasons + severity over trust items (Phase 7)."""

from __future__ import annotations

import uuid

from app.domain.enums import ConfidenceBand, FreshnessBand, RiskBand, SourceType
from app.intelligence.debt import analyze_debt
from app.trust.base import SourceItem


def _item(
    *,
    confidence: float,
    confidence_band: ConfidenceBand,
    freshness_band: FreshnessBand,
    has_owner: bool,
    title: str = "doc",
) -> SourceItem:
    return SourceItem(
        document_id=uuid.uuid4(),
        title=title,
        source_type=SourceType.GITHUB,
        url=None,
        confidence=confidence,
        confidence_band=confidence_band,
        freshness_band=freshness_band,
        age_days=10.0,
        has_owner=has_owner,
    )


def test_clean_document_is_not_debt() -> None:
    report = analyze_debt(
        [
            _item(
                confidence=0.9,
                confidence_band=ConfidenceBand.HIGH,
                freshness_band=FreshnessBand.FRESH,
                has_owner=True,
            )
        ]
    )
    assert report.total_documents == 1
    assert report.debt_count == 0
    assert report.items == []


def test_reasons_are_surfaced() -> None:
    report = analyze_debt(
        [
            _item(
                confidence=0.2,
                confidence_band=ConfidenceBand.LOW,
                freshness_band=FreshnessBand.STALE,
                has_owner=False,
            )
        ]
    )
    assert report.debt_count == 1
    item = report.items[0]
    assert set(item.reasons) == {"low_confidence", "stale", "unowned"}
    assert item.severity_band == RiskBand.HIGH
    assert report.by_reason == {"low_confidence": 1, "stale": 1, "unowned": 1}


def test_severity_orders_worst_first() -> None:
    mild = _item(
        confidence=0.7,
        confidence_band=ConfidenceBand.MEDIUM,
        freshness_band=FreshnessBand.AGING,
        has_owner=True,
        title="mild",
    )
    severe = _item(
        confidence=0.1,
        confidence_band=ConfidenceBand.LOW,
        freshness_band=FreshnessBand.STALE,
        has_owner=False,
        title="severe",
    )
    report = analyze_debt([mild, severe])
    assert report.debt_count == 2
    assert report.items[0].title == "severe"
    assert report.items[0].severity_score > report.items[1].severity_score
    assert sum(report.by_band.values()) == report.debt_count
