"""Reciprocal Rank Fusion (ADR-0016).

RRF combines several ranked lists into one without needing the underlying scores to be
comparable — each list contributes ``1 / (k + rank)`` to every item it ranks. It is the
standard, robust way to blend keyword and vector results, and it is a pure function so
the hybrid ranking is fully unit-testable.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import TypeVar

_DEFAULT_K = 60

T = TypeVar("T")


def reciprocal_rank_fusion(
    ranked_lists: Sequence[Sequence[T]], k: int = _DEFAULT_K
) -> list[tuple[T, float]]:
    """Fuse ranked lists into one list of ``(item, score)`` ordered by score desc.

    ``rank`` is 0-based within each list; ties break on first appearance so the result
    is deterministic.
    """
    scores: dict[T, float] = {}
    order: dict[T, int] = {}
    seen = 0
    for ranked in ranked_lists:
        for rank, item in enumerate(ranked):
            scores[item] = scores.get(item, 0.0) + 1.0 / (k + rank)
            if item not in order:
                order[item] = seen
                seen += 1
    return sorted(scores.items(), key=lambda kv: (-kv[1], order[kv[0]]))
