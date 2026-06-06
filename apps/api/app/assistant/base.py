"""Assistant value objects (Phase 6).

Frozen, store- and schema-agnostic dataclasses shared by the intent classifier, the
answer composer, the service and the serializer — the same layering the retrieval,
graph and trust packages use to keep the engine free of the ORM and Pydantic.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from app.domain.enums import (
    AssistantIntent,
    ConfidenceBand,
    EntityKind,
    FreshnessBand,
    RelationshipType,
    SourceType,
)


@dataclass(frozen=True)
class OwnerRef:
    """An accountable owner attributed from the knowledge graph (ADR-0018)."""

    key: str
    name: str


@dataclass(frozen=True)
class Citation:
    """One evidence passage backing an answer, carrying Phase-5 trust."""

    document_id: uuid.UUID
    title: str
    source_type: SourceType
    url: str | None
    chunk_id: uuid.UUID | None
    ordinal: int | None
    snippet: str
    confidence: float
    confidence_band: ConfidenceBand
    freshness_band: FreshnessBand
    age_days: float | None
    owners: list[OwnerRef]
    ownership_known: bool


@dataclass(frozen=True)
class AnswerEntity:
    """A knowledge-graph entity matched by the question (a structured facet)."""

    key: str
    kind: EntityKind
    name: str
    summary: str | None


@dataclass(frozen=True)
class RelatedFact:
    """A directly-related graph fact about the focus entity (neighborhood edge)."""

    relation: RelationshipType
    direction: str  # "out" (focus -> entity) or "in" (entity -> focus)
    kind: EntityKind
    name: str
    key: str


@dataclass(frozen=True)
class AssistantAnswer:
    """A composed, evidence-backed answer to one question."""

    intent: AssistantIntent
    summary: str
    key_points: list[str]
    citations: list[Citation]
    entities: list[AnswerEntity]
    relations: list[RelatedFact]
    confidence: float
    confidence_band: ConfidenceBand
