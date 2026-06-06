"""Trust API schemas (mirrored in packages/contracts)."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel

from app.domain.enums import ConfidenceBand, FreshnessBand, SourceType
from app.trust.base import (
    FreshnessSummary,
    SourceInfo,
    SourceItem,
    TrustProfile,
)


class OwnerRefOut(BaseModel):
    key: str
    name: str


class SourceInfoOut(BaseModel):
    source_type: SourceType
    connector_id: uuid.UUID
    external_id: str
    title: str
    url: str | None
    source_updated_at: datetime | None
    ingested_at: datetime

    @classmethod
    def from_info(cls, info: SourceInfo) -> SourceInfoOut:
        return cls(
            source_type=info.source_type,
            connector_id=info.connector_id,
            external_id=info.external_id,
            title=info.title,
            url=info.url,
            source_updated_at=info.source_updated_at,
            ingested_at=info.ingested_at,
        )


class EvidenceItemOut(BaseModel):
    chunk_id: uuid.UUID
    ordinal: int
    snippet: str


class TrustProfileResponse(BaseModel):
    document_id: uuid.UUID
    title: str
    confidence: float
    confidence_band: ConfidenceBand
    freshness: float
    freshness_band: FreshnessBand
    age_days: float | None
    signals: dict[str, float]
    source: SourceInfoOut
    owners: list[OwnerRefOut]
    ownership_known: bool
    evidence: list[EvidenceItemOut]

    @classmethod
    def from_profile(cls, profile: TrustProfile) -> TrustProfileResponse:
        return cls(
            document_id=profile.document_id,
            title=profile.title,
            confidence=profile.confidence,
            confidence_band=profile.confidence_band,
            freshness=profile.freshness,
            freshness_band=profile.freshness_band,
            age_days=profile.age_days,
            signals=profile.signals,
            source=SourceInfoOut.from_info(profile.source),
            owners=[OwnerRefOut(key=o.key, name=o.name) for o in profile.owners],
            ownership_known=profile.ownership_known,
            evidence=[
                EvidenceItemOut(
                    chunk_id=e.chunk_id, ordinal=e.ordinal, snippet=e.snippet
                )
                for e in profile.evidence
            ],
        )


class SourceTrustItem(BaseModel):
    document_id: uuid.UUID
    title: str
    source_type: SourceType
    url: str | None
    confidence: float
    confidence_band: ConfidenceBand
    freshness_band: FreshnessBand
    age_days: float | None
    has_owner: bool

    @classmethod
    def from_item(cls, item: SourceItem) -> SourceTrustItem:
        return cls(
            document_id=item.document_id,
            title=item.title,
            source_type=item.source_type,
            url=item.url,
            confidence=item.confidence,
            confidence_band=item.confidence_band,
            freshness_band=item.freshness_band,
            age_days=item.age_days,
            has_owner=item.has_owner,
        )


class SourceListResponse(BaseModel):
    sources: list[SourceTrustItem]


class FreshnessBucketOut(BaseModel):
    band: FreshnessBand
    count: int


class FreshnessResponse(BaseModel):
    total: int
    buckets: list[FreshnessBucketOut]
    stale: list[SourceTrustItem]

    @classmethod
    def from_summary(cls, summary: FreshnessSummary) -> FreshnessResponse:
        return cls(
            total=summary.total,
            buckets=[
                FreshnessBucketOut(band=b.band, count=b.count) for b in summary.buckets
            ],
            stale=[SourceTrustItem.from_item(i) for i in summary.stale],
        )
