"""Parser — normalize raw markdown/HTML content into clean plain text.

Strips the most common markdown/HTML noise (fences, tags, emphasis, list markers,
links → their anchor text) and collapses whitespace, while collecting any URLs for
enrichment. Deterministic and regex-based; a richer per-source parser can replace it.
"""

from __future__ import annotations

import re

from app.processing.base import ParsedDocument

_CODE_FENCE_RE = re.compile(r"```.*?```", re.DOTALL)
_INLINE_CODE_RE = re.compile(r"`([^`]*)`")
_HTML_TAG_RE = re.compile(r"<[^>]+>")
_IMAGE_RE = re.compile(r"!\[[^\]]*\]\([^)]*\)")
_LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
_BARE_URL_RE = re.compile(r"https?://[^\s)]+")
_HEADING_RE = re.compile(r"^\s{0,3}#{1,6}\s*", re.MULTILINE)
_QUOTE_RE = re.compile(r"^\s{0,3}>\s?", re.MULTILINE)
_LIST_MARKER_RE = re.compile(r"^\s{0,3}(?:[-*+]|\d+\.)\s+", re.MULTILINE)
_EMPHASIS_RE = re.compile(r"([*_~]{1,3})(.+?)\1")
_WS_RE = re.compile(r"[ \t]+")
_BLANKLINES_RE = re.compile(r"\n{3,}")


def parse(raw_content: str | None) -> ParsedDocument:
    """Return cleaned text and extracted links from raw source content."""
    text = raw_content or ""
    links = _extract_links(text)

    text = _CODE_FENCE_RE.sub(" ", text)
    text = _IMAGE_RE.sub(" ", text)
    text = _LINK_RE.sub(r"\1", text)  # keep anchor text, drop the URL
    text = _INLINE_CODE_RE.sub(r"\1", text)
    text = _HTML_TAG_RE.sub(" ", text)
    text = _HEADING_RE.sub("", text)
    text = _QUOTE_RE.sub("", text)
    text = _LIST_MARKER_RE.sub("", text)
    text = _EMPHASIS_RE.sub(r"\2", text)

    text = _WS_RE.sub(" ", text)
    text = _BLANKLINES_RE.sub("\n\n", text)
    cleaned = "\n".join(line.strip() for line in text.splitlines())
    return ParsedDocument(text=cleaned.strip(), links=links)


def _extract_links(text: str) -> list[str]:
    """Collect unique URLs (markdown link targets + bare URLs), order preserved."""
    seen: dict[str, None] = {}
    for _, url in _LINK_RE.findall(text):
        seen.setdefault(url.strip(), None)
    for url in _BARE_URL_RE.findall(text):
        seen.setdefault(url.strip(), None)
    return list(seen)
