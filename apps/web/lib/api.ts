import type {
  ChunkStatsResponse,
  Connector,
  ConnectorCatalogResponse,
  ConnectorCreate,
  ConnectorListResponse,
  Document,
  DocumentListResponse,
  DocumentProcessingDetail,
  ProcessedDocument,
  ProcessedDocumentListResponse,
  ProcessingEvent,
  ProcessingEventListResponse,
  ProcessingRun,
  ProcessingRunListResponse,
  ReadinessResponse,
  SourceTypeInfo,
  SyncEvent,
  SyncEventListResponse,
  SyncRun,
  SyncRunListResponse,
} from "@ekip/contracts";

/**
 * Typed server-side client for the EKIP API. Uses the shared contract types so the
 * frontend and backend cannot silently drift (risk R2). Reads never throw; mutations
 * return a discriminated result.
 */
const API_URL = process.env.EKIP_API_URL ?? "http://localhost:8000";

// DEV-ONLY: header principal so the UI works before OAuth/SSO login lands. In
// production the gateway forwards a verified bearer token instead.
const DEV_TENANT = process.env.EKIP_TENANT_ID ?? "public";
const DEV_ROLE = process.env.EKIP_ROLE ?? "editor";

function authHeaders(): Record<string, string> {
  return { "X-Tenant-Id": DEV_TENANT, "X-Role": DEV_ROLE };
}

async function getJson<T>(path: string): Promise<T | null> {
  try {
    const res = await fetch(`${API_URL}${path}`, {
      cache: "no-store",
      headers: authHeaders(),
    });
    if (!res.ok) return null;
    return (await res.json()) as T;
  } catch {
    return null;
  }
}

export interface MutationResult {
  ok: boolean;
  error?: string;
}

async function postJson(path: string, body?: unknown): Promise<MutationResult> {
  try {
    const res = await fetch(`${API_URL}${path}`, {
      method: "POST",
      cache: "no-store",
      headers: { ...authHeaders(), "Content-Type": "application/json" },
      body: body === undefined ? undefined : JSON.stringify(body),
    });
    if (!res.ok) {
      const detail = (await res.json().catch(() => null)) as { detail?: string } | null;
      return { ok: false, error: detail?.detail ?? `Request failed (${res.status})` };
    }
    return { ok: true };
  } catch {
    return { ok: false, error: "API unreachable" };
  }
}

export interface ReadinessResult {
  reachable: boolean;
  data: ReadinessResponse | null;
}

/** Fetch backend readiness. Never throws — returns reachable=false when the API is down. */
export async function fetchReadiness(): Promise<ReadinessResult> {
  try {
    const res = await fetch(`${API_URL}/health/ready`, { cache: "no-store" });
    const data = (await res.json()) as ReadinessResponse;
    return { reachable: true, data };
  } catch {
    return { reachable: false, data: null };
  }
}

export async function fetchCatalog(): Promise<SourceTypeInfo[]> {
  return (await getJson<ConnectorCatalogResponse>("/connectors/catalog"))?.sources ?? [];
}

export async function fetchConnectors(): Promise<Connector[]> {
  return (await getJson<ConnectorListResponse>("/connectors"))?.connectors ?? [];
}

export async function fetchConnector(id: string): Promise<Connector | null> {
  return getJson<Connector>(`/connectors/${id}`);
}

export async function fetchSyncRuns(connectorId?: string): Promise<SyncRun[]> {
  const query = connectorId ? `?connector_id=${connectorId}` : "";
  return (await getJson<SyncRunListResponse>(`/sync/runs${query}`))?.runs ?? [];
}

export async function fetchSyncRun(id: string): Promise<SyncRun | null> {
  return getJson<SyncRun>(`/sync/runs/${id}`);
}

export async function fetchSyncEvents(runId: string): Promise<SyncEvent[]> {
  return (await getJson<SyncEventListResponse>(`/sync/runs/${runId}/events`))?.events ?? [];
}

export async function fetchDocuments(connectorId?: string): Promise<Document[]> {
  const query = connectorId ? `?connector_id=${connectorId}` : "";
  return (await getJson<DocumentListResponse>(`/documents${query}`))?.documents ?? [];
}

export async function createConnector(input: ConnectorCreate): Promise<MutationResult> {
  return postJson("/connectors", input);
}

export async function triggerSync(connectorId: string): Promise<MutationResult> {
  return postJson(`/connectors/${connectorId}/sync`);
}

// --- Phase 2: Knowledge Processing ---

export async function fetchProcessingStats(): Promise<ChunkStatsResponse | null> {
  return getJson<ChunkStatsResponse>("/processing/stats");
}

export async function fetchProcessingRuns(): Promise<ProcessingRun[]> {
  return (await getJson<ProcessingRunListResponse>("/processing/runs"))?.runs ?? [];
}

export async function fetchProcessingRun(id: string): Promise<ProcessingRun | null> {
  return getJson<ProcessingRun>(`/processing/runs/${id}`);
}

export async function fetchProcessingEvents(runId: string): Promise<ProcessingEvent[]> {
  return (
    (await getJson<ProcessingEventListResponse>(`/processing/runs/${runId}/events`))
      ?.events ?? []
  );
}

export async function fetchProcessedDocuments(): Promise<ProcessedDocument[]> {
  return (
    (await getJson<ProcessedDocumentListResponse>("/processing/documents"))?.documents ??
    []
  );
}

export async function fetchDocumentProcessing(
  id: string,
): Promise<DocumentProcessingDetail | null> {
  return getJson<DocumentProcessingDetail>(`/processing/documents/${id}`);
}

export async function triggerProcessing(): Promise<MutationResult> {
  return postJson("/processing/runs");
}
