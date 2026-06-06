"""GitHub connector tests — parsing, PR skipping, cursor advancement.

Uses httpx.MockTransport so no network is required.
"""

from __future__ import annotations

import httpx

from app.connectors.github import GitHubConnector

_ISSUE = {
    "number": 1,
    "title": "Login fails",
    "body": "Steps to reproduce",
    "html_url": "https://github.com/o/r/issues/1",
    "state": "open",
    "labels": [{"name": "bug"}],
    "user": {"login": "alice"},
    "comments": 3,
    "updated_at": "2024-01-01T00:00:00Z",
}
_PULL_REQUEST = {
    "number": 2,
    "title": "Fix login",
    "pull_request": {"url": "..."},
    "updated_at": "2024-01-02T00:00:00Z",
}


async def test_fetch_parses_issues_and_skips_prs() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.params.get("page") == "1":
            return httpx.Response(200, json=[_ISSUE, _PULL_REQUEST])
        return httpx.Response(200, json=[])

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        connector = GitHubConnector("o", "r", "token", client)
        result = await connector.fetch(None)

    assert len(result.documents) == 1
    doc = result.documents[0]
    assert doc.external_id == "1"
    assert doc.title == "Login fails"
    assert doc.metadata["labels"] == ["bug"]
    assert doc.metadata["author"] == "alice"
    # Cursor advances to the latest *issue* timestamp, ignoring the PR.
    assert result.cursor == "2024-01-01T00:00:00Z"


async def test_fetch_sends_since_for_incremental() -> None:
    seen: dict[str, str | None] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["since"] = request.url.params.get("since")
        return httpx.Response(200, json=[])

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        connector = GitHubConnector("o", "r", "token", client)
        await connector.fetch("2024-01-01T00:00:00Z")

    assert seen["since"] == "2024-01-01T00:00:00Z"
