"""Trust engine — assembles confidence/freshness/ownership/source for documents.

Read-only and deterministic (ADR-0017): every method computes from current state, so
there is no trust persistence to go stale. Confidence and freshness come from the pure
``scoring`` module; ownership is attributed from the knowledge graph's ``modified``
edges (ADR-0018) — never guessed. Powers the Trust Inspector (one document),
Source Explorer (provenance list) and Freshness Dashboard (corpus distribution).
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from app.domain.enums import (
    EntityKind,
    FreshnessBand,
    ProcessingStatus,
    RelationshipType,
    SourceType,
)
from app.graph.base import entity_key
from app.graph.store import GraphStore
from app.models.document import Document
from app.repositories.chunks import ChunkRepository
from app.repositories.trust import TrustRepository, TrustRow
from app.trust import scoring
from app.trust.base import (
    EvidenceItem,
    FreshnessBucket,
    FreshnessSummary,
    OwnerRef,
    SourceInfo,
    SourceItem,
    TrustProfile,
    TrustSignals,
)

_SNIPPET_CHARS = 240
_EVIDENCE = 5
_STALE_LIMIT = 10
_CORPUS_LIMIT = 10_000
_DOC_KEY_PREFIX = f"{EntityKind.DOCUMENT.value}:"


def _now() -> datetime:
    return datetime.now(UTC)


class TrustService:
    def __init__(
        self,
        trust_repo: TrustRepository,
        chunk_repo: ChunkRepository,
        graph_store: GraphStore,
    ) -> None:
        self._trust = trust_repo
        self._chunks = chunk_repo
        self._graph = graph_store

    async def profile(
        self, tenant_id: str, document_id: uuid.UUID
    ) -> TrustProfile | None:
        row = await self._trust.get_document(tenant_id, document_id)
        if row is None:
            return None
        document, enrichment, embedding = row
        owners = await self._owners(tenant_id, document_id)
        signals = _signals(row, has_owner=bool(owners), now=_now())
        score, contributions = scoring.confidence(signals)
        chunks = await self._chunks.list_by_document(tenant_id, document_id)
        evidence = [
            EvidenceItem(chunk_id=c.id, ordinal=c.ordinal, snippet=_snippet(c.content))
            for c in chunks[:_EVIDENCE]
        ]
        return TrustProfile(
            document_id=document.id,
            title=document.title,
            confidence=score,
            confidence_band=scoring.confidence_band(score),
            freshness=scoring.freshness_score(signals.age_days),
            freshness_band=scoring.freshness_band(signals.age_days),
            age_days=_round_age(signals.age_days),
            signals=contributions,
            source=_source_info(document),
            owners=owners,
            ownership_known=bool(owners),
            evidence=evidence,
        )

    async def sources(
        self,
        tenant_id: str,
        source_type: SourceType | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[SourceItem]:
        rows = await self._trust.list_documents(tenant_id, source_type, limit, offset)
        owned = await self._owned_document_keys(tenant_id)
        now = _now()
        return [self._item(row, owned, now) for row in rows]

    async def freshness(self, tenant_id: str) -> FreshnessSummary:
        rows = await self._trust.list_documents(tenant_id, None, _CORPUS_LIMIT, 0)
        owned = await self._owned_document_keys(tenant_id)
        now = _now()
        items = [self._item(row, owned, now) for row in rows]

        counts: dict[FreshnessBand, int] = dict.fromkeys(FreshnessBand, 0)
        for item in items:
            counts[item.freshness_band] += 1
        buckets = [FreshnessBucket(band=b, count=counts[b]) for b in FreshnessBand]

        stale = [
            item
            for item in items
            if item.freshness_band in (FreshnessBand.AGING, FreshnessBand.STALE)
        ]
        stale.sort(key=lambda i: (i.age_days is None, -(i.age_days or 0.0)))
        return FreshnessSummary(total=len(items), buckets=buckets, stale=stale[:_STALE_LIMIT])

    def _item(
        self, row: TrustRow, owned: set[str], now: datetime
    ) -> SourceItem:
        document = row[0]
        has_owner = entity_key(EntityKind.DOCUMENT, str(document.id)) in owned
        signals = _signals(row, has_owner=has_owner, now=now)
        score, _ = scoring.confidence(signals)
        return SourceItem(
            document_id=document.id,
            title=document.title,
            source_type=document.source_type,
            url=document.url,
            confidence=score,
            confidence_band=scoring.confidence_band(score),
            freshness_band=scoring.freshness_band(signals.age_days),
            age_days=_round_age(signals.age_days),
            has_owner=has_owner,
        )

    async def _owners(
        self, tenant_id: str, document_id: uuid.UUID
    ) -> list[OwnerRef]:
        doc_key = entity_key(EntityKind.DOCUMENT, str(document_id))
        neighborhood = await self._graph.neighborhood(tenant_id, doc_key)
        if neighborhood is None:
            return []
        owners: list[OwnerRef] = []
        seen: set[str] = set()
        for neighbor in neighborhood.neighbors:
            if (
                neighbor.type == RelationshipType.MODIFIED
                and neighbor.direction == "in"
                and neighbor.entity.kind == EntityKind.ENGINEER
                and neighbor.entity.key not in seen
            ):
                seen.add(neighbor.entity.key)
                owners.append(OwnerRef(key=neighbor.entity.key, name=neighbor.entity.name))
        owners.sort(key=lambda o: o.name.lower())
        return owners

    async def _owned_document_keys(self, tenant_id: str) -> set[str]:
        """Document keys with at least one engineer ``modified`` edge (one query).

        Avoids a per-document neighborhood lookup for list/aggregate views. Filtering
        by the document key prefix keeps it correct regardless of whether a store
        populates edge endpoint metadata.
        """
        rels = await self._graph.list_relationships(
            tenant_id, RelationshipType.MODIFIED, limit=_CORPUS_LIMIT
        )
        return {r.to_key for r in rels if r.to_key.startswith(_DOC_KEY_PREFIX)}


def _signals(row: TrustRow, *, has_owner: bool, now: datetime) -> TrustSignals:
    document, enrichment, embedding = row
    timestamp = document.source_updated_at or document.updated_at
    return TrustSignals(
        processed=enrichment is not None
        and enrichment.status == ProcessingStatus.PROCESSED,
        embedded=embedding is not None,
        has_owner=has_owner,
        chunk_count=enrichment.chunk_count if enrichment else 0,
        word_count=enrichment.word_count if enrichment else 0,
        age_days=scoring.age_in_days(timestamp, now),
    )


def _source_info(document: Document) -> SourceInfo:
    return SourceInfo(
        source_type=document.source_type,
        connector_id=document.connector_id,
        external_id=document.external_id,
        title=document.title,
        url=document.url,
        source_updated_at=document.source_updated_at,
        ingested_at=document.updated_at,
    )


def _round_age(age_days: float | None) -> float | None:
    return round(age_days, 1) if age_days is not None else None


def _snippet(content: str) -> str:
    text = " ".join(content.split())
    return text[:_SNIPPET_CHARS] + ("…" if len(text) > _SNIPPET_CHARS else "")
