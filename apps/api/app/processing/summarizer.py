"""Summarizer — extractive summary of parsed text (Phase 2).

Scores sentences by the frequency of their salient (non-stopword) terms and returns
the top few in their original order. Extractive + deterministic, so summaries are
stable and require no model provider; an abstractive summarizer can replace it later.
"""

from __future__ import annotations

from collections import Counter

from app.processing.text import split_sentences, tokenize

DEFAULT_MAX_SENTENCES = 3
_MAX_SUMMARY_CHARS = 600


def summarize(text: str, max_sentences: int = DEFAULT_MAX_SENTENCES) -> str:
    """Return an extractive summary of at most ``max_sentences`` sentences."""
    sentences = split_sentences(text)
    if len(sentences) <= max_sentences:
        return _truncate(" ".join(sentences))

    frequencies = Counter(tokenize(text))
    if not frequencies:
        return _truncate(" ".join(sentences[:max_sentences]))

    # Rank by score, then earlier sentences first for stable tie-breaking.
    scored = [
        (_score(sentence, frequencies), -index, index)
        for index, sentence in enumerate(sentences)
    ]
    top = sorted(scored, reverse=True)[:max_sentences]
    chosen = sorted(index for _, _, index in top)
    return _truncate(" ".join(sentences[i] for i in chosen))


def _score(sentence: str, frequencies: Counter[str]) -> int:
    return sum(frequencies[token] for token in tokenize(sentence))


def _truncate(text: str) -> str:
    if len(text) <= _MAX_SUMMARY_CHARS:
        return text
    return text[: _MAX_SUMMARY_CHARS - 1].rstrip() + "…"
