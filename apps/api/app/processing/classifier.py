"""Classifier — assign a heuristic category to a document (Phase 2).

Source labels (e.g. GitHub issue labels) are the strongest signal and are checked
first; otherwise a small keyword scan over title + text decides. Deterministic and
ordered by priority. A model-based classifier can replace this behind ``classify``.
"""

from __future__ import annotations

from typing import Any

from app.domain.enums import DocumentCategory

# Label substring → category (checked against source-provided labels first).
_LABEL_RULES: list[tuple[tuple[str, ...], DocumentCategory]] = [
    (("incident", "outage", "sev", "postmortem"), DocumentCategory.INCIDENT),
    (("bug", "defect", "regression"), DocumentCategory.BUG),
    (("feature", "enhancement", "improvement"), DocumentCategory.FEATURE),
    (("question", "support", "help"), DocumentCategory.QUESTION),
    (("doc", "documentation"), DocumentCategory.DOCUMENTATION),
    (("discussion", "rfc", "proposal"), DocumentCategory.DISCUSSION),
]

# Keyword substring → category (fallback scan over title + body).
_KEYWORD_RULES: list[tuple[tuple[str, ...], DocumentCategory]] = [
    (("incident", "outage", "postmortem", "downtime"), DocumentCategory.INCIDENT),
    (("error", "crash", "broken", "fails", "exception", "stack trace"), DocumentCategory.BUG),
    (("how do i", "how to", "what is", "?"), DocumentCategory.QUESTION),
    (("add support", "implement", "feature request", "would be nice"), DocumentCategory.FEATURE),
    (("documentation", "readme", "guide", "tutorial"), DocumentCategory.DOCUMENTATION),
    (("proposal", "rfc", "discuss"), DocumentCategory.DISCUSSION),
]


def classify(title: str, text: str, metadata: dict[str, Any] | None = None) -> DocumentCategory:
    """Return the best-effort category for a document."""
    labels = _labels(metadata)
    for needles, category in _LABEL_RULES:
        if any(any(n in label for n in needles) for label in labels):
            return category

    haystack = f"{title}\n{text}".lower()
    for needles, category in _KEYWORD_RULES:
        if any(n in haystack for n in needles):
            return category
    return DocumentCategory.OTHER


def _labels(metadata: dict[str, Any] | None) -> list[str]:
    """Extract lowercased label strings from source metadata, if present."""
    if not metadata:
        return []
    raw = metadata.get("labels")
    if not isinstance(raw, list):
        return []
    labels: list[str] = []
    for item in raw:
        if isinstance(item, str):
            labels.append(item.lower())
        elif isinstance(item, dict) and isinstance(item.get("name"), str):
            labels.append(item["name"].lower())
    return labels
