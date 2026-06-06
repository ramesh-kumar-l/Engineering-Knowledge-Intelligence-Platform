"""Unit tests for the deterministic processing pipeline (no database)."""

from __future__ import annotations

from app.domain.enums import DocumentCategory
from app.processing import chunker, classifier, enricher, parser, pipeline, summarizer


def test_parser_strips_markdown_and_collects_links() -> None:
    raw = (
        "# Title\n\n"
        "Some **bold** and `code` and a [link](https://example.com).\n"
        "```python\nignored = 1\n```\n"
        "> a quote\n- item one\n"
    )
    parsed = parser.parse(raw)
    assert "#" not in parsed.text
    assert "**" not in parsed.text
    assert "```" not in parsed.text
    assert "link" in parsed.text and "https://example.com" not in parsed.text
    assert "https://example.com" in parsed.links


def test_parser_handles_empty() -> None:
    parsed = parser.parse(None)
    assert parsed.text == ""
    assert parsed.links == []


def test_chunker_respects_budget_and_overlap() -> None:
    text = " ".join(f"word{i}" for i in range(400))
    chunks = chunker.chunk(text, max_chars=200, overlap_chars=40)
    assert len(chunks) > 1
    assert all(c.char_count <= 200 for c in chunks)
    assert [c.ordinal for c in chunks] == list(range(len(chunks)))
    # Overlap: the start of chunk 2 repeats some tail of chunk 1.
    assert chunks[1].content.split()[0] in chunks[0].content.split()


def test_chunker_empty_text() -> None:
    assert chunker.chunk("") == []


def test_classifier_prefers_labels() -> None:
    category = classifier.classify(
        "Anything", "body", {"labels": ["bug", "priority-high"]}
    )
    assert category == DocumentCategory.BUG


def test_classifier_keyword_fallback() -> None:
    assert classifier.classify("App crashed", "stack trace here") == DocumentCategory.BUG
    assert classifier.classify("How to deploy?", "") == DocumentCategory.QUESTION
    assert classifier.classify("Random note", "nothing here") == DocumentCategory.OTHER


def test_enricher_extracts_keywords_and_counts() -> None:
    result = enricher.enrich("database database database connection pooling matters")
    assert result.keywords[0] == "database"
    assert result.word_count == 6
    assert result.language == "unknown" or result.language == "en"


def test_summarizer_is_extractive_and_bounded() -> None:
    text = (
        "The cache layer reduces latency. "
        "Latency matters for the cache and users. "
        "Unrelated trivia about weather. "
        "Cache invalidation is hard."
    )
    summary = summarizer.summarize(text, max_sentences=2)
    assert "cache" in summary.lower()
    assert len(summary) <= len(text)


def test_pipeline_produces_full_output() -> None:
    output = pipeline.process(
        "Login bug", "Users report the login page **crashes** intermittently.", {}
    )
    assert output.category == DocumentCategory.BUG
    assert output.summary
    assert output.chunks
    assert output.enrichment.word_count > 0
