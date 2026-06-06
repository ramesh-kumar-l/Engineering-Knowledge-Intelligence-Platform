"""Deterministic trust scoring (ADR-0017).

Pure functions — no I/O, no models — so they are fully unit-testable and reproducible,
mirroring ``retrieval.fusion``/``retrieval.keyword``. ``confidence`` blends five
signals with fixed weights; ``freshness_*`` derive an age-based score and band. The
weights/thresholds are heuristics (documented as tech debt), tunable here in one place.
"""

from __future__ import annotations

from datetime import UTC, datetime

from app.domain.enums import ConfidenceBand, FreshnessBand
from app.trust.base import TrustSignals

# Freshness band thresholds (days since the source was last updated).
_FRESH_DAYS = 30.0
_RECENT_DAYS = 90.0
_STALE_DAYS = 365.0
# Linear freshness decay: score reaches 0 at ~18 months.
_DECAY_DAYS = 540.0

# Confidence weights (sum to 1.0). Each component contributes in [0, 1].
_WEIGHTS: dict[str, float] = {
    "freshness": 0.30,
    "ownership": 0.20,
    "processed": 0.20,
    "embedded": 0.15,
    "richness": 0.15,
}
# Chunks for full corroboration credit (more substance => higher confidence).
_RICHNESS_TARGET = 5

# Confidence band thresholds.
_HIGH = 0.75
_MEDIUM = 0.45


def age_in_days(ts: datetime | None, now: datetime) -> float | None:
    """Whole-and-fractional days between ``ts`` and ``now`` (None if no timestamp)."""
    if ts is None:
        return None
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=UTC)
    return max((now - ts).total_seconds() / 86400.0, 0.0)


def freshness_score(age_days: float | None) -> float:
    """Linear decay in [0, 1]; unknown age scores 0 (transparent uncertainty)."""
    if age_days is None:
        return 0.0
    return round(max(0.0, 1.0 - age_days / _DECAY_DAYS), 4)


def freshness_band(age_days: float | None) -> FreshnessBand:
    if age_days is None or age_days > _STALE_DAYS:
        return FreshnessBand.STALE
    if age_days <= _FRESH_DAYS:
        return FreshnessBand.FRESH
    if age_days <= _RECENT_DAYS:
        return FreshnessBand.RECENT
    return FreshnessBand.AGING


def richness_score(chunk_count: int) -> float:
    if chunk_count <= 0:
        return 0.0
    return round(min(chunk_count / _RICHNESS_TARGET, 1.0), 4)


def confidence_components(signals: TrustSignals) -> dict[str, float]:
    """Each signal normalised to [0, 1] before weighting (for the inspector)."""
    return {
        "freshness": freshness_score(signals.age_days),
        "ownership": 1.0 if signals.has_owner else 0.0,
        "processed": 1.0 if signals.processed else 0.0,
        "embedded": 1.0 if signals.embedded else 0.0,
        "richness": richness_score(signals.chunk_count),
    }


def confidence(signals: TrustSignals) -> tuple[float, dict[str, float]]:
    """Weighted confidence in [0, 1] plus the per-signal contribution breakdown.

    Contributions sum to the returned score, so the Trust Inspector can show exactly
    why an answer is (un)trusted.
    """
    components = confidence_components(signals)
    contributions = {k: round(_WEIGHTS[k] * v, 4) for k, v in components.items()}
    score = round(sum(contributions.values()), 4)
    return score, contributions


def confidence_band(score: float) -> ConfidenceBand:
    if score >= _HIGH:
        return ConfidenceBand.HIGH
    if score >= _MEDIUM:
        return ConfidenceBand.MEDIUM
    return ConfidenceBand.LOW
