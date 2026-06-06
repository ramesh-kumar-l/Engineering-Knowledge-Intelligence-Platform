"""Source-type catalog — what the Connector Catalog screen lists.

GitHub is implemented in Phase 1; the remaining sources are registered as catalog
entries (``implemented=False``) so the roadmap is visible and they can be enabled
incrementally without touching the API surface.
"""

from __future__ import annotations

from app.connectors.base import ConfigField, ConnectorSpec
from app.domain.enums import SourceType

_GITHUB = ConnectorSpec(
    source_type=SourceType.GITHUB,
    label="GitHub",
    description="Ingest issues from a GitHub repository.",
    implemented=True,
    config_fields=[
        ConfigField(key="owner", label="Repository owner"),
        ConfigField(key="repo", label="Repository name"),
    ],
    secret_label="Personal access token",
)


def _planned(source_type: SourceType, label: str, description: str) -> ConnectorSpec:
    return ConnectorSpec(
        source_type=source_type,
        label=label,
        description=description,
        implemented=False,
    )


CATALOG: tuple[ConnectorSpec, ...] = (
    _GITHUB,
    _planned(SourceType.GITLAB, "GitLab", "Ingest issues and merge requests."),
    _planned(SourceType.JIRA, "Jira", "Ingest issues and projects."),
    _planned(SourceType.CONFLUENCE, "Confluence", "Ingest spaces and pages."),
    _planned(SourceType.SLACK, "Slack", "Ingest channel message threads."),
    _planned(SourceType.NOTION, "Notion", "Ingest workspaces and pages."),
)

_BY_TYPE = {spec.source_type: spec for spec in CATALOG}


def get_spec(source_type: SourceType) -> ConnectorSpec:
    return _BY_TYPE[source_type]
