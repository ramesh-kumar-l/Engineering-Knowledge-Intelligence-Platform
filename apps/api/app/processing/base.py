"""Shared dataclasses for the processing pipeline.

These are storage-agnostic value objects passed between pipeline steps and returned
to the service, which maps them onto ORM models. Keeping them separate from the ORM
lets each step stay a pure function that is trivial to unit-test.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.domain.enums import DocumentCategory


@dataclass(frozen=True)
class ParsedDocument:
    """Cleaned plain text extracted from raw (markdown/HTML) source content."""

    text: str
    links: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ChunkData:
    """One retrievable chunk produced by the chunker."""

    ordinal: int
    content: str
    char_count: int
    token_estimate: int


@dataclass(frozen=True)
class EnrichmentResult:
    """Lightweight metadata derived from the parsed text."""

    keywords: list[str]
    language: str | None
    word_count: int
    char_count: int


@dataclass(frozen=True)
class ProcessingOutput:
    """Full result of processing one document — mapped onto ORM by the service."""

    category: DocumentCategory
    summary: str
    enrichment: EnrichmentResult
    chunks: list[ChunkData]
