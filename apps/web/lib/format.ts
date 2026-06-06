import type {
  AssistantIntent,
  ConfidenceBand,
  ConnectorStatus,
  DocumentCategory,
  EntityKind,
  FreshnessBand,
  ProcessingStatus,
  RelationshipType,
  RiskBand,
  SyncStatus,
} from "@ekip/contracts";

import type { Tone } from "@/components/badge";

export function connectorTone(status: ConnectorStatus): Tone {
  if (status === "active") return "success";
  if (status === "error") return "danger";
  return "warning";
}

export function syncTone(status: SyncStatus): Tone {
  if (status === "succeeded") return "success";
  if (status === "failed") return "danger";
  return "info";
}

export function processingStatusTone(status: ProcessingStatus): Tone {
  if (status === "processed") return "success";
  if (status === "failed") return "danger";
  return "muted";
}

const CATEGORY_TONE: Record<DocumentCategory, Tone> = {
  bug: "danger",
  incident: "danger",
  feature: "info",
  question: "warning",
  documentation: "success",
  discussion: "muted",
  other: "muted",
};

export function categoryTone(category: DocumentCategory): Tone {
  return CATEGORY_TONE[category];
}

const ENTITY_KIND_TONE: Record<EntityKind, Tone> = {
  engineer: "info",
  team: "info",
  repository: "success",
  service: "warning",
  api: "warning",
  incident: "danger",
  adr: "muted",
  document: "muted",
};

export function entityKindTone(kind: EntityKind): Tone {
  return ENTITY_KIND_TONE[kind];
}

const RELATIONSHIP_LABEL: Record<RelationshipType, string> = {
  owns: "owns",
  depends_on: "depends on",
  modified: "modified",
  impacts: "impacts",
  resolved: "resolved",
};

export function relationshipLabel(type: RelationshipType): string {
  return RELATIONSHIP_LABEL[type];
}

const CONFIDENCE_TONE: Record<ConfidenceBand, Tone> = {
  high: "success",
  medium: "warning",
  low: "danger",
};

export function confidenceTone(band: ConfidenceBand): Tone {
  return CONFIDENCE_TONE[band];
}

const FRESHNESS_TONE: Record<FreshnessBand, Tone> = {
  fresh: "success",
  recent: "info",
  aging: "warning",
  stale: "danger",
};

export function freshnessTone(band: FreshnessBand): Tone {
  return FRESHNESS_TONE[band];
}

const INTENT_LABEL: Record<AssistantIntent, string> = {
  service: "Service",
  ownership: "Ownership",
  incident: "Incident",
  architecture: "Architecture",
  general: "General",
};

export function intentLabel(intent: AssistantIntent): string {
  return INTENT_LABEL[intent];
}

const RISK_TONE: Record<RiskBand, Tone> = {
  high: "danger",
  medium: "warning",
  low: "success",
};

export function riskTone(band: RiskBand): Tone {
  return RISK_TONE[band];
}

const DEBT_REASON_LABEL: Record<string, string> = {
  low_confidence: "low confidence",
  stale: "stale",
  unowned: "unowned",
};

export function debtReasonLabel(reason: string): string {
  return DEBT_REASON_LABEL[reason] ?? reason;
}

export function formatPercent(ratio: number): string {
  return `${Math.round(ratio * 100)}%`;
}

export function formatDate(iso: string | null): string {
  if (!iso) return "—";
  return new Date(iso).toLocaleString();
}

export function formatAge(days: number | null): string {
  if (days === null) return "unknown";
  if (days < 1) return "today";
  if (days < 30) return `${Math.round(days)}d ago`;
  if (days < 365) return `${Math.round(days / 30)}mo ago`;
  return `${(days / 365).toFixed(1)}y ago`;
}
