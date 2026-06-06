import type { ConnectorStatus, SyncStatus } from "@ekip/contracts";

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

export function formatDate(iso: string | null): string {
  if (!iso) return "—";
  return new Date(iso).toLocaleString();
}
