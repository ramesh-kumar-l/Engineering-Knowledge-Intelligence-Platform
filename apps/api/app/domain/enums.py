"""Shared domain enums for the ingestion layer (Phase 1).

Centralized so models, connectors, services and schemas agree on the same string
values. Stored as plain strings in PostgreSQL (portable, no DB enum migrations).
"""

from __future__ import annotations

from enum import StrEnum


class SourceType(StrEnum):
    """Knowledge sources EKIP can ingest from (roadmap Phase 1)."""

    GITHUB = "github"
    GITLAB = "gitlab"
    JIRA = "jira"
    CONFLUENCE = "confluence"
    SLACK = "slack"
    NOTION = "notion"


class ConnectorStatus(StrEnum):
    ACTIVE = "active"
    PAUSED = "paused"
    ERROR = "error"


class SyncStatus(StrEnum):
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class SyncEventLevel(StrEnum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class ChangeType(StrEnum):
    """Outcome of reconciling one source document during a sync."""

    CREATED = "created"
    UPDATED = "updated"
    UNCHANGED = "unchanged"
    DELETED = "deleted"
