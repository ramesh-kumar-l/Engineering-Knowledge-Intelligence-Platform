import type {
  ConnectorStatus,
  DocumentCategory,
  ProcessingStatus,
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

export function formatDate(iso: string | null): string {
  if (!iso) return "—";
  return new Date(iso).toLocaleString();
}
