"""Shared, deterministic composition helpers for the agents (Phase 8).

Keeps the individual planners small: evidence gathering (hybrid retrieval + Phase-5
trust per cited document), confidence aggregation, graph owner lookup and mapping a
technical-debt item to evidence. Pure composition over the existing services — no model
provider, no I/O of its own beyond the layers it calls.
"""

from __future__ import annotations

import uuid

from app.agents.base import AgentEvidence
from app.agents.context import AgentContext
from app.domain.enums import ConfidenceBand, EntityKind, RelationshipType
from app.intelligence.base import DebtItem
from app.trust.base import TrustProfile
from app.trust.scoring import confidence_band

_SNIPPET_CHARS = 240


async def gather_evidence(
    ctx: AgentContext, query: str, limit: int
) -> list[AgentEvidence]:
    """Hybrid-retrieve for ``query`` and attach trust to each cited document.

    Trust profiles are fetched once per document (mirrors the assistant), so this stays
    cheap for a handful of hits. Returns at most one evidence item per document.
    """
    query = query.strip()
    if not query:
        return []
    result = await ctx.search.search(ctx.tenant_id, query, "hybrid", limit)
    profiles: dict[uuid.UUID, TrustProfile | None] = {}
    evidence: list[AgentEvidence] = []
    seen: set[uuid.UUID] = set()
    for hit in result.chunks:
        if hit.document_id in seen:
            continue
        if hit.document_id not in profiles:
            profiles[hit.document_id] = await ctx.trust.profile(
                ctx.tenant_id, hit.document_id
            )
        profile = profiles[hit.document_id]
        if profile is None:
            continue
        seen.add(hit.document_id)
        evidence.append(_from_profile(profile, hit.snippet))
    return evidence


def _from_profile(profile: TrustProfile, snippet: str) -> AgentEvidence:
    return AgentEvidence(
        document_id=profile.document_id,
        title=profile.title,
        source_type=profile.source.source_type,
        url=profile.source.url,
        snippet=_clip(snippet),
        confidence=profile.confidence,
        confidence_band=profile.confidence_band,
        freshness_band=profile.freshness_band,
        age_days=profile.age_days,
        owners=[o.name for o in profile.owners],
        ownership_known=profile.ownership_known,
    )


def evidence_from_debt(items: list[DebtItem]) -> list[AgentEvidence]:
    """Map technical-debt items straight to evidence (no re-retrieval needed)."""
    return [
        AgentEvidence(
            document_id=i.document_id,
            title=i.title,
            source_type=i.source_type,
            url=i.url,
            snippet=", ".join(i.reasons) or "flagged",
            confidence=i.confidence,
            confidence_band=i.confidence_band,
            freshness_band=i.freshness_band,
            age_days=i.age_days,
            owners=[],
            ownership_known=i.has_owner,
        )
        for i in items
    ]


def mean_confidence(evidence: list[AgentEvidence]) -> tuple[float, ConfidenceBand]:
    """Overall confidence = mean of cited evidence confidence (else zero)."""
    if not evidence:
        return 0.0, confidence_band(0.0)
    score = round(sum(e.confidence for e in evidence) / len(evidence), 4)
    return score, confidence_band(score)


async def owners_of(ctx: AgentContext, key: str) -> list[str]:
    """Owner names of a graph entity via ``owns``/``modified`` incoming edges."""
    neighborhood = await ctx.graph.neighborhood(ctx.tenant_id, key)
    if neighborhood is None:
        return []
    names: list[str] = []
    seen: set[str] = set()
    for neighbor in neighborhood.neighbors:
        if (
            neighbor.direction == "in"
            and neighbor.type in (RelationshipType.OWNS, RelationshipType.MODIFIED)
            and neighbor.entity.kind in (EntityKind.ENGINEER, EntityKind.TEAM)
            and neighbor.entity.key not in seen
        ):
            seen.add(neighbor.entity.key)
            names.append(neighbor.entity.name)
    names.sort(key=str.lower)
    return names


def matches(target: str, *fields: str) -> bool:
    """Case-insensitive substring match of ``target`` against any field."""
    needle = target.strip().lower()
    if not needle:
        return False
    return any(needle in (f or "").lower() for f in fields)


def _clip(text: str) -> str:
    text = " ".join(text.split())
    return text[:_SNIPPET_CHARS] + ("…" if len(text) > _SNIPPET_CHARS else "")
