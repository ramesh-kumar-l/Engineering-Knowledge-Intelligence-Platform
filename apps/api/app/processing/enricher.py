"""Enricher — derive lightweight metadata from parsed text (Phase 2).

Extracts the most frequent salient terms (keywords), counts, and a coarse language
guess. Deterministic frequency analysis with stable tie-breaking by first appearance.
"""

from __future__ import annotations

from collections import Counter

from app.processing.base import EnrichmentResult
from app.processing.text import STOPWORDS, tokenize

_MAX_KEYWORDS = 10


def enrich(text: str) -> EnrichmentResult:
    """Return keywords, language and size metrics for ``text``."""
    tokens = tokenize(text)
    keywords = _top_keywords(tokens)
    return EnrichmentResult(
        keywords=keywords,
        language=_guess_language(text, tokens),
        word_count=len(text.split()),
        char_count=len(text),
    )


def _top_keywords(tokens: list[str]) -> list[str]:
    if not tokens:
        return []
    # Order of first appearance breaks frequency ties deterministically.
    first_seen = {tok: i for i, tok in enumerate(reversed(tokens))}
    counts = Counter(tokens)
    ranked = sorted(counts, key=lambda t: (-counts[t], -first_seen[t]))
    return ranked[:_MAX_KEYWORDS]


def _guess_language(text: str, tokens: list[str]) -> str | None:
    """Coarse heuristic: English if any common stopword appears, else unknown."""
    if not text.strip():
        return None
    words = {m.lower() for m in text.split()}
    return "en" if words & STOPWORDS else "unknown"
