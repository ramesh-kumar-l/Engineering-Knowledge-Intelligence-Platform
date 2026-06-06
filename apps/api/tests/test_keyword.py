"""Keyword scoring unit tests."""

from __future__ import annotations

from app.retrieval import keyword


def test_query_terms_drops_short_tokens() -> None:
    assert keyword.query_terms("a payment Service!") == ["payment", "service"]


def test_title_match_boosted_over_body() -> None:
    terms = keyword.query_terms("payment")
    body_only = keyword.score("the payment failed", "Login bug", terms)
    title_match = keyword.score("the failed", "Payment outage", terms)
    assert title_match > body_only


def test_no_terms_scores_zero() -> None:
    assert keyword.score("anything here", "title", []) == 0.0
