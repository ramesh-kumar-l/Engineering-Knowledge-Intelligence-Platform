"""Deterministic answer composition (Phase 6, ADR-0019).

Assembles an answer from retrieved evidence + graph facts — extractive and templated,
never generative (no model provider). The overall answer confidence is the mean of the
cited documents' Phase-5 confidence, so every answer carries trust. Pure: no I/O.
"""

from __future__ import annotations

from app.assistant.base import (
    AnswerEntity,
    AssistantAnswer,
    Citation,
    RelatedFact,
)
from app.domain.enums import AssistantIntent, RelationshipType
from app.trust.scoring import confidence_band

_MAX_EVIDENCE_POINTS = 3
_MAX_RELATION_POINTS = 4
_MAX_OWNERS = 3
_SENTENCE_CHARS = 180

_EMPTY = (
    "I could not find supporting evidence in the current knowledge base for this "
    "question. Try ingesting more sources, building the graph/index, or rephrasing."
)

_RELATION_LABEL: dict[RelationshipType, str] = {
    RelationshipType.OWNS: "owns",
    RelationshipType.DEPENDS_ON: "depends on",
    RelationshipType.MODIFIED: "was modified by",
    RelationshipType.IMPACTS: "impacts",
    RelationshipType.RESOLVED: "was resolved by",
}


def compose(
    intent: AssistantIntent,
    question: str,
    citations: list[Citation],
    entities: list[AnswerEntity],
    relations: list[RelatedFact],
    focus_name: str | None,
) -> AssistantAnswer:
    """Build an evidence-backed answer; confidence is the mean of cited trust."""
    confidence = (
        round(sum(c.confidence for c in citations) / len(citations), 4)
        if citations
        else 0.0
    )
    band = confidence_band(confidence)

    if not citations and not entities:
        return AssistantAnswer(
            intent=intent,
            summary=_EMPTY,
            key_points=[],
            citations=[],
            entities=[],
            relations=[],
            confidence=0.0,
            confidence_band=band,
        )

    owners = _owners(citations)
    return AssistantAnswer(
        intent=intent,
        summary=_summary(intent, len(citations), owners, focus_name, confidence, band.value),
        key_points=_key_points(intent, citations, owners, relations, focus_name),
        citations=citations,
        entities=entities,
        relations=relations,
        confidence=confidence,
        confidence_band=band,
    )


def _summary(
    intent: AssistantIntent,
    n: int,
    owners: list[str],
    focus: str | None,
    confidence: float,
    band: str,
) -> str:
    note = f" Overall confidence: {band} ({confidence:.2f})."
    focus_note = f" Focus: {focus}." if focus else ""
    if intent == AssistantIntent.OWNERSHIP:
        if owners:
            lead = (
                f"{_join(owners)} appear most accountable, based on who modified the "
                "most relevant sources."
            )
        else:
            lead = (
                "No ownership signals were found in the knowledge graph for the most "
                "relevant sources."
            )
        return lead + note
    if intent == AssistantIntent.INCIDENT:
        return f"Found {n} related source(s) for this incident question.{focus_note}{note}"
    if intent == AssistantIntent.ARCHITECTURE:
        return f"Drawing on {n} source(s) and related context.{focus_note}{note}"
    if intent == AssistantIntent.SERVICE:
        lead = f"Based on {n} source(s), here is what the knowledge base describes."
        return f"{lead}{focus_note}{note}"
    return f"Here is what I found across {n} source(s).{note}"


def _key_points(
    intent: AssistantIntent,
    citations: list[Citation],
    owners: list[str],
    relations: list[RelatedFact],
    focus: str | None,
) -> list[str]:
    points: list[str] = []
    if intent == AssistantIntent.OWNERSHIP:
        points.append(
            "Owners: " + _join(owners)
            if owners
            else "Ownership unknown for the cited sources."
        )
    points.extend(_evidence_points(citations))
    if intent in (
        AssistantIntent.INCIDENT,
        AssistantIntent.ARCHITECTURE,
        AssistantIntent.SERVICE,
    ):
        points.extend(_relation_points(relations, focus))
    if intent != AssistantIntent.OWNERSHIP and owners:
        points.append("Likely owners: " + _join(owners))
    return points


def _evidence_points(citations: list[Citation]) -> list[str]:
    return [
        f"{c.title}: {_first_sentence(c.snippet)}"
        for c in citations[:_MAX_EVIDENCE_POINTS]
    ]


def _relation_points(relations: list[RelatedFact], focus: str | None) -> list[str]:
    if focus is None:
        return []
    out: list[str] = []
    for rel in relations[:_MAX_RELATION_POINTS]:
        label = _RELATION_LABEL.get(rel.relation, rel.relation.value)
        if rel.direction == "out":
            out.append(f"{focus} {label} {rel.name}")
        else:
            out.append(f"{rel.name} {label} {focus}")
    return out


def _owners(citations: list[Citation]) -> list[str]:
    names: list[str] = []
    seen: set[str] = set()
    for citation in citations:
        for owner in citation.owners:
            if owner.key not in seen:
                seen.add(owner.key)
                names.append(owner.name)
    return names


def _join(names: list[str]) -> str:
    shown = names[:_MAX_OWNERS]
    extra = len(names) - len(shown)
    if not shown:
        return "no one identified"
    if len(shown) == 1:
        base = shown[0]
    else:
        base = ", ".join(shown[:-1]) + f" and {shown[-1]}"
    return base + (f" (+{extra} more)" if extra > 0 else "")


def _first_sentence(text: str) -> str:
    text = " ".join(text.split())
    for sep in (". ", "! ", "? "):
        idx = text.find(sep)
        if 0 <= idx <= _SENTENCE_CHARS:
            return text[: idx + 1]
    return text[:_SENTENCE_CHARS] + ("…" if len(text) > _SENTENCE_CHARS else "")
