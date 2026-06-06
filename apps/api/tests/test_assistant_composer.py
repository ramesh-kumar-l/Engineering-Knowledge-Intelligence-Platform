"""Assistant composer — deterministic, evidence-backed answer assembly."""

from __future__ import annotations

import uuid

from app.assistant.base import AnswerEntity, Citation, OwnerRef, RelatedFact
from app.assistant.composer import compose
from app.domain.enums import (
    AssistantIntent,
    ConfidenceBand,
    EntityKind,
    FreshnessBand,
    RelationshipType,
    SourceType,
)


def _citation(confidence: float, *, owner: str | None = None) -> Citation:
    return Citation(
        document_id=uuid.uuid4(),
        title="Checkout architecture",
        source_type=SourceType.GITHUB,
        url=None,
        chunk_id=uuid.uuid4(),
        ordinal=0,
        snippet="Checkout orchestrates payment capture. It calls the ledger service.",
        confidence=confidence,
        confidence_band=ConfidenceBand.HIGH,
        freshness_band=FreshnessBand.FRESH,
        age_days=3.0,
        owners=[OwnerRef(key="engineer:octocat", name="octocat")] if owner else [],
        ownership_known=owner is not None,
    )


def test_confidence_is_mean_of_citations() -> None:
    answer = compose(
        AssistantIntent.SERVICE,
        "How does checkout work?",
        [_citation(0.8), _citation(0.6)],
        [],
        [],
        None,
    )
    assert answer.confidence == 0.7
    assert answer.confidence_band == ConfidenceBand.MEDIUM
    assert answer.key_points  # evidence points present
    assert "2 source(s)" in answer.summary


def test_empty_evidence_is_honest() -> None:
    answer = compose(AssistantIntent.GENERAL, "anything", [], [], [], None)
    assert answer.confidence == 0.0
    assert answer.citations == []
    assert "could not find" in answer.summary.lower()


def test_ownership_surfaces_owners() -> None:
    answer = compose(
        AssistantIntent.OWNERSHIP,
        "Who owns checkout?",
        [_citation(0.9, owner="octocat")],
        [],
        [],
        None,
    )
    assert "octocat" in answer.summary
    assert any("octocat" in point for point in answer.key_points)


def test_ownership_unknown_is_stated() -> None:
    answer = compose(
        AssistantIntent.OWNERSHIP, "Who owns checkout?", [_citation(0.5)], [], [], None
    )
    assert "no ownership" in answer.summary.lower()
    assert any("unknown" in point.lower() for point in answer.key_points)


def test_relations_render_with_direction() -> None:
    entity = AnswerEntity(
        key="service:checkout", kind=EntityKind.SERVICE, name="checkout", summary=None
    )
    relations = [
        RelatedFact(
            relation=RelationshipType.DEPENDS_ON,
            direction="out",
            kind=EntityKind.SERVICE,
            name="ledger",
            key="service:ledger",
        )
    ]
    answer = compose(
        AssistantIntent.ARCHITECTURE,
        "what does checkout depend on",
        [_citation(0.7)],
        [entity],
        relations,
        "checkout",
    )
    assert any("checkout depends on ledger" in point for point in answer.key_points)
