"""Pure scoring helpers shared by the intelligence analyzers (Phase 7, ADR-0020).

Deterministic and explainable: a saturating ratio for unbounded counts, a clamp to
keep scores in ``[0, 1]``, and fixed band thresholds. No models, no calibration —
the heuristic weights live in the analyzers; this module only normalizes and bands.
"""

from __future__ import annotations

from app.domain.enums import RiskBand

_HIGH = 0.66
_MEDIUM = 0.33


def saturate(count: int, ceiling: int) -> float:
    """Map a non-negative count into ``[0, 1]``, saturating at ``ceiling``."""
    if ceiling <= 0:
        return 0.0
    return min(1.0, count / ceiling)


def clamp(value: float) -> float:
    return max(0.0, min(1.0, value))


def risk_band(score: float) -> RiskBand:
    if score >= _HIGH:
        return RiskBand.HIGH
    if score >= _MEDIUM:
        return RiskBand.MEDIUM
    return RiskBand.LOW
