"""Pipeline — compose the processing steps into one pure function.

``process`` runs parse → enrich → classify → summarize → chunk over a single
document's raw content and returns a :class:`ProcessingOutput`. It performs no I/O,
so the service layer can call it per document and persist the result.
"""

from __future__ import annotations

from typing import Any

from app.processing import chunker, classifier, enricher, parser, summarizer
from app.processing.base import ProcessingOutput


def process(
    title: str,
    raw_content: str | None,
    metadata: dict[str, Any] | None = None,
) -> ProcessingOutput:
    """Run the full processing pipeline for one document."""
    parsed = parser.parse(raw_content)
    enrichment = enricher.enrich(parsed.text)
    category = classifier.classify(title, parsed.text, metadata)
    summary = summarizer.summarize(parsed.text)
    chunks = chunker.chunk(parsed.text)
    return ProcessingOutput(
        category=category,
        summary=summary,
        enrichment=enrichment,
        chunks=chunks,
    )
