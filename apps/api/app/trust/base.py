"""Trust primitives shared by the scorer, service and API layer (Phase 5).

Frozen, store-agnostic dataclasses — the same layering ``app/retrieval/base.py`` and
``app/graph/base.py`` use to keep the service free of both the ORM and the Pydantic
schemas.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime

from app.domain.enums import ConfidenceBand, FreshnessBand, SourceType


@dataclass(frozen=True)
class TrustSignals:
    """Raw inputs the deterministic scorer blends into a confidence score."""

    processed: bool
    embedded: bool
    has_owner: bool
    chunk_count: int
    word_count: int
    age_days: float | None


@dataclass(frozen=True)
class SourceInfo:
    """Provenance of a document — answers "where did this come from?"."""

    source_type: SourceType
    connector_id: uuid.UUID
    external_id: str
    title: str
    url: str | None
    source_updated_at: datetime | None
    ingested_at: datetime


@dataclass(frozen=True)
class OwnerRef:
    """An accountable owner attributed from the knowledge graph."""

    key: str
    name: str


@dataclass(frozen=True)
class EvidenceItem:
    """A document excerpt backing the answer (supporting evidence)."""

    chunk_id: uuid.UUID
    ordinal: int
    snippet: str


@dataclass(frozen=True)
class TrustProfile:
    """The full trust picture for one document (Trust Inspector)."""

    document_id: uuid.UUID
    title: str
    confidence: float
    confidence_band: ConfidenceBand
    freshness: float
    freshness_band: FreshnessBand
    age_days: float | None
    signals: dict[str, float]
    source: SourceInfo
    owners: list[OwnerRef]
    ownership_known: bool
    evidence: list[EvidenceItem]


@dataclass(frozen=True)
class SourceItem:
    """A document row with its trust bands (Source Explorer / Freshness lists)."""

    document_id: uuid.UUID
    title: str
    source_type: SourceType
    url: str | None
    confidence: float
    confidence_band: ConfidenceBand
    freshness_band: FreshnessBand
    age_days: float | None
    has_owner: bool


@dataclass(frozen=True)
class FreshnessBucket:
    band: FreshnessBand
    count: int


@dataclass(frozen=True)
class FreshnessSummary:
    """Corpus-wide freshness distribution + the documents most needing attention."""

    total: int
    buckets: list[FreshnessBucket] = field(default_factory=list)
    stale: list[SourceItem] = field(default_factory=list)
