"""Deterministic intent classification (Phase 6, ADR-0019).

Maps a free-text question to one of the assistant's capability intents using an
ordered keyword heuristic — no model provider, so the same question always resolves
to the same intent. The order encodes precedence when a question spans concerns
(e.g. an ownership question about a service is treated as ownership). An LLM-backed
classifier is a planned upgrade behind this same seam.
"""

from __future__ import annotations

from app.domain.enums import AssistantIntent

# (intent, trigger terms). First intent with any matching term wins.
_RULES: list[tuple[AssistantIntent, tuple[str, ...]]] = [
    (
        AssistantIntent.OWNERSHIP,
        (
            "who owns",
            "who own",
            "owner",
            "responsible",
            "maintainer",
            "who maintains",
            "who wrote",
            "who built",
            "who can i ask",
            "accountable",
        ),
    ),
    (
        AssistantIntent.INCIDENT,
        (
            "incident",
            "outage",
            "postmortem",
            "post-mortem",
            "root cause",
            "what caused",
            "downtime",
            "went down",
            "failure",
            "regression",
            "broke",
        ),
    ),
    (
        AssistantIntent.ARCHITECTURE,
        (
            "why was",
            "why did",
            "why do",
            "architecture",
            "design decision",
            "adr",
            "trade-off",
            "tradeoff",
            "depends on",
            "depend on",
            "dependency",
            "rationale",
            "decided",
        ),
    ),
    (
        AssistantIntent.SERVICE,
        (
            "how does",
            "how do",
            "what is",
            "what does",
            "explain",
            "overview",
            "works",
            "service",
            "endpoint",
            "api",
        ),
    ),
]


def classify(question: str) -> AssistantIntent:
    """Resolve a question to its capability intent (defaults to GENERAL)."""
    text = question.lower()
    for intent, terms in _RULES:
        if any(term in text for term in terms):
            return intent
    return AssistantIntent.GENERAL
