"""Assistant intent classification — deterministic keyword routing."""

from __future__ import annotations

import pytest

from app.assistant.intent import classify
from app.domain.enums import AssistantIntent


@pytest.mark.parametrize(
    ("question", "expected"),
    [
        ("Who owns the checkout service?", AssistantIntent.OWNERSHIP),
        ("Who is responsible for the billing API?", AssistantIntent.OWNERSHIP),
        ("What caused the payments outage last week?", AssistantIntent.INCIDENT),
        ("Show me the postmortem for the incident", AssistantIntent.INCIDENT),
        ("Why was the event-driven architecture chosen?", AssistantIntent.ARCHITECTURE),
        ("What does the checkout service depend on?", AssistantIntent.ARCHITECTURE),
        ("How does the checkout service work?", AssistantIntent.SERVICE),
        ("Explain the search endpoint", AssistantIntent.SERVICE),
        ("Tell me about onboarding", AssistantIntent.GENERAL),
    ],
)
def test_classify(question: str, expected: AssistantIntent) -> None:
    assert classify(question) == expected


def test_ownership_precedes_service() -> None:
    # A question that mentions both ownership and a service resolves to ownership.
    assert classify("Who owns the checkout service?") == AssistantIntent.OWNERSHIP
