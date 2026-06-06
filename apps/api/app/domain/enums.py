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


class ProcessingStatus(StrEnum):
    """Per-document state in the Phase 2 processing pipeline."""

    PENDING = "pending"
    PROCESSED = "processed"
    FAILED = "failed"


class DocumentCategory(StrEnum):
    """Heuristic classification of a document's intent (Phase 2)."""

    BUG = "bug"
    FEATURE = "feature"
    QUESTION = "question"
    INCIDENT = "incident"
    DOCUMENTATION = "documentation"
    DISCUSSION = "discussion"
    OTHER = "other"


class EntityKind(StrEnum):
    """Knowledge-graph node kinds (Phase 3, domain_model.md)."""

    ENGINEER = "engineer"
    TEAM = "team"
    REPOSITORY = "repository"
    SERVICE = "service"
    API = "api"
    INCIDENT = "incident"
    ADR = "adr"
    DOCUMENT = "document"


class RelationshipType(StrEnum):
    """Knowledge-graph edge types (Phase 3, domain_model.md)."""

    OWNS = "owns"
    DEPENDS_ON = "depends_on"
    MODIFIED = "modified"
    IMPACTS = "impacts"
    RESOLVED = "resolved"


class GraphSource(StrEnum):
    """How a graph node/edge entered the graph."""

    PROJECTION = "projection"  # deterministically derived from ingested data
    MANUAL = "manual"  # curated by an editor via the API


class ConfidenceBand(StrEnum):
    """Coarse trust band for a confidence score (Phase 5, trust_framework.md)."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class FreshnessBand(StrEnum):
    """How current a document's underlying knowledge is (Phase 5)."""

    FRESH = "fresh"  # recently updated at the source
    RECENT = "recent"
    AGING = "aging"
    STALE = "stale"  # old or unknown last-updated time


class RiskBand(StrEnum):
    """Coarse severity band for an intelligence risk score (Phase 7).

    Higher is worse — the inverse of ``ConfidenceBand`` — used for dependency risk
    and technical-debt severity.
    """

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class AssistantIntent(StrEnum):
    """What an engineering question is asking for (Phase 6, roadmap capabilities)."""

    SERVICE = "service"  # how a service/component works
    OWNERSHIP = "ownership"  # who owns / is accountable
    INCIDENT = "incident"  # what caused / how an incident was handled
    ARCHITECTURE = "architecture"  # why a design/decision was made
    GENERAL = "general"  # fallback knowledge lookup


class MessageRole(StrEnum):
    """Author of a conversation message (Phase 6)."""

    USER = "user"
    ASSISTANT = "assistant"
