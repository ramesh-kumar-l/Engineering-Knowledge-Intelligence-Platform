"""Deterministic text embedder (ADR-0014).

``HashingEmbedder`` turns text into a fixed-dimension unit vector with signed feature
hashing — no external model, no network, no API key, fully reproducible. Cosine
similarity between two such vectors approximates weighted token overlap, which is good
enough for semantic-ish recall in the first retrieval increment and keeps tests
offline. The ``Embedder`` protocol is the seam: a model-backed embedder (OpenAI,
sentence-transformers, …) can replace this without touching the stores or services.
"""

from __future__ import annotations

import hashlib
import math
import re
from typing import Protocol, runtime_checkable

_TOKEN_RE = re.compile(r"[a-z0-9]+")
_DEFAULT_DIM = 256


def _tokens(text: str) -> list[str]:
    return [t for t in _TOKEN_RE.findall(text.lower()) if len(t) >= 2]


@runtime_checkable
class Embedder(Protocol):
    """Maps text to a fixed-length embedding vector."""

    @property
    def dimension(self) -> int: ...

    @property
    def name(self) -> str: ...

    def embed(self, text: str) -> list[float]: ...

    def embed_batch(self, texts: list[str]) -> list[list[float]]: ...


class HashingEmbedder:
    """Signed feature-hashing embedder. Deterministic and dependency-free."""

    def __init__(self, dimension: int = _DEFAULT_DIM) -> None:
        self._dim = dimension

    @property
    def dimension(self) -> int:
        return self._dim

    @property
    def name(self) -> str:
        return f"hashing-{self._dim}"

    def embed(self, text: str) -> list[float]:
        vec = [0.0] * self._dim
        for token in _tokens(text):
            digest = hashlib.md5(token.encode("utf-8")).digest()
            bucket = int.from_bytes(digest[:4], "big") % self._dim
            sign = 1.0 if digest[4] & 1 else -1.0
            vec[bucket] += sign
        norm = math.sqrt(sum(value * value for value in vec))
        if norm == 0.0:
            return vec
        return [value / norm for value in vec]

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [self.embed(text) for text in texts]
