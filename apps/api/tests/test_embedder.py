"""Embedder unit tests — determinism, dimension, normalization, similarity ordering."""

from __future__ import annotations

import math

from app.retrieval.embedder import HashingEmbedder


def test_dimension_and_determinism() -> None:
    embedder = HashingEmbedder(dimension=128)
    a = embedder.embed("the quick brown fox")
    b = embedder.embed("the quick brown fox")
    assert len(a) == 128
    assert a == b


def test_unit_normalized() -> None:
    vec = HashingEmbedder().embed("payments service handles refunds")
    assert math.isclose(math.sqrt(sum(x * x for x in vec)), 1.0, rel_tol=1e-6)


def test_empty_text_is_zero_vector() -> None:
    vec = HashingEmbedder(dimension=64).embed("")
    assert vec == [0.0] * 64


def test_similar_text_scores_higher() -> None:
    embedder = HashingEmbedder()

    def cosine(x: list[float], y: list[float]) -> float:
        return sum(a * b for a, b in zip(x, y, strict=True))

    query = embedder.embed("incident in the payment service")
    near = embedder.embed("the payment service had an incident")
    far = embedder.embed("frontend button color tokens")
    assert cosine(query, near) > cosine(query, far)
