"""Deterministic keyword scoring over candidate chunks (Phase 4).

The repository fetches candidate chunks with a tenant-scoped ``LIKE`` over the query
terms (portable across PostgreSQL and the SQLite test engine); this pure function then
ranks them by term frequency, with a small boost for matches in the title. Keeping the
ranking in Python makes it unit-testable and keeps parity between prod and tests.
A production upgrade to PostgreSQL full-text search (``tsvector``/GIN) slots in behind
the same repository seam.
"""

from __future__ import annotations

import re

_TOKEN_RE = re.compile(r"[a-z0-9]+")
_TITLE_BOOST = 2.0


def query_terms(query: str) -> list[str]:
    return [t for t in _TOKEN_RE.findall(query.lower()) if len(t) >= 2]


def score(content: str, title: str, terms: list[str]) -> float:
    if not terms:
        return 0.0
    body = content.lower()
    head = title.lower()
    total = 0.0
    for term in terms:
        total += float(body.count(term))
        total += _TITLE_BOOST * float(head.count(term))
    return total
