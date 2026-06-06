"""GitHub connector — ingests repository issues incrementally (Phase 1).

Uses the REST issues API with ``since`` for incremental sync and ``sort=updated`` so
the cursor (last seen ``updated_at``) advances monotonically. Pull requests are
skipped; only issues are ingested. The httpx client is injected for testability.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

import httpx

from app.connectors.base import Connector, FetchResult, RawDocument
from app.domain.enums import SourceType

_API_BASE = "https://api.github.com"
_PER_PAGE = 100
_MAX_PAGES = 10  # bound one sync to 1000 issues; the cursor resumes the rest.


def _parse_ts(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


class GitHubConnector:
    source_type = SourceType.GITHUB

    def __init__(self, owner: str, repo: str, token: str, client: httpx.AsyncClient) -> None:
        self._owner = owner
        self._repo = repo
        self._token = token
        self._client = client

    def _to_document(self, issue: dict[str, Any]) -> RawDocument:
        body = issue.get("body") or ""
        title = issue["title"]
        labels = [label["name"] for label in issue.get("labels", [])]
        return RawDocument(
            external_id=str(issue["number"]),
            title=title,
            content=f"{title}\n\n{body}".strip(),
            url=issue.get("html_url"),
            metadata={
                "state": issue.get("state"),
                "labels": labels,
                "author": (issue.get("user") or {}).get("login"),
                "comments": issue.get("comments", 0),
            },
            source_updated_at=_parse_ts(issue.get("updated_at")),
        )

    async def fetch(self, cursor: str | None) -> FetchResult:
        headers = {
            "Authorization": f"Bearer {self._token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        url = f"{_API_BASE}/repos/{self._owner}/{self._repo}/issues"
        documents: list[RawDocument] = []
        latest = cursor

        for page in range(1, _MAX_PAGES + 1):
            params: dict[str, str | int] = {
                "state": "all",
                "sort": "updated",
                "direction": "asc",
                "per_page": _PER_PAGE,
                "page": page,
            }
            if cursor:
                params["since"] = cursor
            resp = await self._client.get(url, params=params, headers=headers)
            resp.raise_for_status()
            issues = resp.json()
            if not issues:
                break
            for issue in issues:
                if "pull_request" in issue:  # the issues API also lists PRs.
                    continue
                documents.append(self._to_document(issue))
                latest = issue.get("updated_at") or latest
            if len(issues) < _PER_PAGE:
                break

        return FetchResult(documents=documents, cursor=latest)


def build(config: dict[str, Any], secret: str | None, client: httpx.AsyncClient) -> Connector:
    """Factory used by the connector registry."""
    owner = config.get("owner")
    repo = config.get("repo")
    if not owner or not repo:
        raise ValueError("GitHub connector requires 'owner' and 'repo' config")
    if not secret:
        raise ValueError("GitHub connector requires an access token")
    return GitHubConnector(owner=owner, repo=repo, token=secret, client=client)
