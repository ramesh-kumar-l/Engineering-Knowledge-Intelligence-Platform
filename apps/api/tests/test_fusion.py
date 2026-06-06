"""Reciprocal rank fusion unit tests."""

from __future__ import annotations

from app.retrieval.fusion import reciprocal_rank_fusion


def test_item_in_both_lists_outranks_single_list_item() -> None:
    fused = reciprocal_rank_fusion([["a", "b", "c"], ["b", "d"]])
    ranked = [item for item, _ in fused]
    assert ranked[0] == "b"  # appears high in both lists


def test_preserves_all_items() -> None:
    fused = dict(reciprocal_rank_fusion([["a", "b"], ["c"]]))
    assert set(fused) == {"a", "b", "c"}


def test_deterministic_tie_break_on_first_appearance() -> None:
    # "x" and "y" each appear once at rank 0 → equal score; "x" seen first.
    fused = reciprocal_rank_fusion([["x"], ["y"]])
    assert [item for item, _ in fused] == ["x", "y"]
