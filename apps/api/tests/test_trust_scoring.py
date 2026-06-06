"""Deterministic trust scoring tests (pure functions, no I/O)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from app.domain.enums import ConfidenceBand, FreshnessBand
from app.trust import scoring
from app.trust.base import TrustSignals


def _signals(
    *,
    processed: bool = True,
    embedded: bool = True,
    has_owner: bool = True,
    chunk_count: int = 5,
    word_count: int = 500,
    age_days: float | None = 0.0,
) -> TrustSignals:
    return TrustSignals(
        processed=processed,
        embedded=embedded,
        has_owner=has_owner,
        chunk_count=chunk_count,
        word_count=word_count,
        age_days=age_days,
    )


def test_age_in_days_handles_naive_and_future() -> None:
    now = datetime(2026, 6, 6, tzinfo=UTC)
    naive = datetime(2026, 5, 7)  # 30 days earlier, no tzinfo
    assert scoring.age_in_days(naive, now) == 30.0
    assert scoring.age_in_days(now + timedelta(days=5), now) == 0.0  # clamped
    assert scoring.age_in_days(None, now) is None


def test_freshness_score_decays_and_floors() -> None:
    assert scoring.freshness_score(0.0) == 1.0
    assert scoring.freshness_score(540.0) == 0.0
    assert scoring.freshness_score(9999.0) == 0.0
    assert scoring.freshness_score(None) == 0.0
    assert 0.0 < scoring.freshness_score(270.0) < 1.0


def test_freshness_bands() -> None:
    assert scoring.freshness_band(10.0) == FreshnessBand.FRESH
    assert scoring.freshness_band(60.0) == FreshnessBand.RECENT
    assert scoring.freshness_band(200.0) == FreshnessBand.AGING
    assert scoring.freshness_band(400.0) == FreshnessBand.STALE
    assert scoring.freshness_band(None) == FreshnessBand.STALE


def test_confidence_contributions_sum_to_score() -> None:
    score, contributions = scoring.confidence(_signals())
    assert score == round(sum(contributions.values()), 4)
    assert score == 1.0  # all signals maxed
    assert scoring.confidence_band(score) == ConfidenceBand.HIGH


def test_low_confidence_for_unprocessed_unowned_stale_doc() -> None:
    score, _ = scoring.confidence(
        _signals(
            processed=False,
            embedded=False,
            has_owner=False,
            chunk_count=0,
            age_days=400.0,
        )
    )
    assert scoring.confidence_band(score) == ConfidenceBand.LOW


def test_confidence_band_thresholds() -> None:
    assert scoring.confidence_band(0.75) == ConfidenceBand.HIGH
    assert scoring.confidence_band(0.45) == ConfidenceBand.MEDIUM
    assert scoring.confidence_band(0.44) == ConfidenceBand.LOW
