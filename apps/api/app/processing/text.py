"""Shared text primitives — tokenization, sentence splitting, stopwords.

Deterministic, regex-based helpers reused by the enricher, summarizer and classifier
so they agree on what a word/sentence is. Intentionally small and English-leaning;
language-aware tokenization can replace this without touching callers.
"""

from __future__ import annotations

import re

_WORD_RE = re.compile(r"[A-Za-z][A-Za-z0-9'+-]*")
# Split on sentence terminators followed by whitespace; keeps newlines as breaks too.
_SENTENCE_RE = re.compile(r"(?<=[.!?])\s+|\n+")

# Compact English stopword set — enough to make keyword/summary signal useful.
STOPWORDS: frozenset[str] = frozenset(
    """
    a an and are as at be been being but by for from had has have he her his i if in
    into is it its of on or our that the their them then there these they this to was
    we were what when which who will with would you your about above after again all
    also am any because before below between both can did do does doing down during
    each few further here how more most no nor not now off once only other out over own
    same should so some such than too under until up very while
    """.split()
)


def tokenize(text: str) -> list[str]:
    """Lowercased word tokens (letters/digits), stopwords excluded."""
    return [
        token
        for token in (m.group(0).lower() for m in _WORD_RE.finditer(text))
        if token not in STOPWORDS and len(token) > 2
    ]


def split_sentences(text: str) -> list[str]:
    """Split text into trimmed, non-empty sentences."""
    return [s.strip() for s in _SENTENCE_RE.split(text) if s.strip()]
