"""Chunker — split cleaned text into overlapping, retrieval-sized chunks.

A word-boundary sliding window keeps chunks under a character budget with a small
overlap so context isn't lost at boundaries (important for later embedding/retrieval).
Token counts are estimated (~4 chars/token) to avoid a tokenizer dependency.
"""

from __future__ import annotations

from app.processing.base import ChunkData

DEFAULT_MAX_CHARS = 1000
DEFAULT_OVERLAP_CHARS = 150


def _estimate_tokens(char_count: int) -> int:
    return max(1, char_count // 4)


def chunk(
    text: str,
    max_chars: int = DEFAULT_MAX_CHARS,
    overlap_chars: int = DEFAULT_OVERLAP_CHARS,
) -> list[ChunkData]:
    """Split ``text`` into ordered chunks no larger than ``max_chars``.

    Splits on whitespace so words are never cut; each chunk after the first repeats
    up to ``overlap_chars`` of trailing context from the previous one.
    """
    words = text.split()
    if not words:
        return []
    if overlap_chars >= max_chars:  # guard against a degenerate config
        overlap_chars = max_chars // 4

    chunks: list[str] = []
    current: list[str] = []
    current_len = 0
    for word in words:
        addition = len(word) + (1 if current else 0)
        if current and current_len + addition > max_chars:
            chunks.append(" ".join(current))
            current = _overlap_tail(current, overlap_chars)
            current_len = sum(len(w) + 1 for w in current)
        current.append(word)
        current_len += len(word) + (1 if current_len else 0)
    if current:
        chunks.append(" ".join(current))

    return [
        ChunkData(
            ordinal=i,
            content=content,
            char_count=len(content),
            token_estimate=_estimate_tokens(len(content)),
        )
        for i, content in enumerate(chunks)
    ]


def _overlap_tail(words: list[str], overlap_chars: int) -> list[str]:
    """Return the trailing words whose combined length fits within ``overlap_chars``."""
    if overlap_chars <= 0:
        return []
    tail: list[str] = []
    length = 0
    for word in reversed(words):
        length += len(word) + 1
        if length > overlap_chars:
            break
        tail.insert(0, word)
    return tail
