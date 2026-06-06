"""JSON serialization of an AssistantAnswer for message persistence (ADR-0019).

Keeps the service free of Pydantic: the answer snapshot is stored as a JSON dict on
the assistant message and rehydrated for Conversation History / Evidence Viewer. The
produced shape matches ``app/domain/assistant.AnswerBody`` exactly, so the route can
validate it directly on read.
"""

from __future__ import annotations

from typing import Any

from app.assistant.base import AssistantAnswer, Citation


def to_dict(answer: AssistantAnswer) -> dict[str, Any]:
    """A JSON-safe snapshot of the answer.

    Enum-typed fields are stringified rather than ``.value``-accessed: some (the
    trust bands) are real ``StrEnum`` members, while ``source_type`` arrives from the
    DB as a plain string. ``str()`` yields the wire value for both.
    """
    return {
        "intent": str(answer.intent),
        "summary": answer.summary,
        "key_points": list(answer.key_points),
        "confidence": answer.confidence,
        "confidence_band": str(answer.confidence_band),
        "citations": [_citation(c) for c in answer.citations],
        "entities": [
            {
                "key": e.key,
                "kind": str(e.kind),
                "name": e.name,
                "summary": e.summary,
            }
            for e in answer.entities
        ],
        "relations": [
            {
                "relation": str(r.relation),
                "direction": r.direction,
                "kind": str(r.kind),
                "name": r.name,
                "key": r.key,
            }
            for r in answer.relations
        ],
    }


def _citation(c: Citation) -> dict[str, Any]:
    return {
        "document_id": str(c.document_id),
        "title": c.title,
        "source_type": str(c.source_type),
        "url": c.url,
        "chunk_id": str(c.chunk_id) if c.chunk_id is not None else None,
        "ordinal": c.ordinal,
        "snippet": c.snippet,
        "confidence": c.confidence,
        "confidence_band": str(c.confidence_band),
        "freshness_band": str(c.freshness_band),
        "age_days": c.age_days,
        "owners": [{"key": o.key, "name": o.name} for o in c.owners],
        "ownership_known": c.ownership_known,
    }
