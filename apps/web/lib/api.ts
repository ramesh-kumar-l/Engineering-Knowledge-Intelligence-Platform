import type {
  AgentCatalogResponse,
  AgentRunDetailResponse,
  AgentRunListResponse,
  AgentRunSummary,
  AgentType,
  AgentTypeInfo,
  AskResponse,
  ChunkStatsResponse,
  Connector,
  ConnectorCatalogResponse,
  ConnectorCreate,
  ConnectorListResponse,
  ConversationDetailResponse,
  ConversationListResponse,
  ConversationSummary,
  DebtReportResponse,
  DependencyReportResponse,
  Document,
  DocumentListResponse,
  DocumentProcessingDetail,
  EmbeddingEvent,
  EmbeddingEventListResponse,
  EmbeddingRun,
  EmbeddingRunListResponse,
  EmbeddingStatsResponse,
  EntityCreateRequest,
  FreshnessResponse,
  GraphBuildEvent,
  GraphBuildEventListResponse,
  GraphBuildRun,
  GraphBuildRunListResponse,
  GraphEntity,
  GraphEntityListResponse,
  GraphNeighborhoodResponse,
  GraphRelationship,
  GraphRelationshipListResponse,
  GraphStatsResponse,
  IncidentReportResponse,
  OverviewResponse,
  OwnershipReportResponse,
  ProcessedDocument,
  ProcessedDocumentListResponse,
  ProcessingEvent,
  ProcessingEventListResponse,
  ProcessingRun,
  ProcessingRunListResponse,
  ReadinessResponse,
  RelationshipCreateRequest,
  RelationshipType,
  SearchMode,
  SearchResponse,
  SourceListResponse,
  SourceTrustItem,
  SourceTypeInfo,
  TrustProfileResponse,
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

/** POST that returns a typed JSON body (null on failure). For read-write endpoints
 * whose response the caller needs, e.g. asking the assistant. */
async function postJsonFor<T>(path: string, body: unknown): Promise<T | null> {
  try {
    const res = await fetch(`${API_URL}${path}`, {
      method: "POST",
      cache: "no-store",
      headers: { ...authHeaders(), "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    if (!res.ok) return null;
    return (await res.json()) as T;
  } catch {
    return null;
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

// --- Phase 3: Knowledge Graph ---

export async function fetchGraphStats(): Promise<GraphStatsResponse | null> {
  return getJson<GraphStatsResponse>("/graph/stats");
}

export async function fetchGraphEntities(
  kind?: string,
  search?: string,
): Promise<GraphEntity[]> {
  const params = new URLSearchParams();
  if (kind) params.set("kind", kind);
  if (search) params.set("search", search);
  const query = params.toString() ? `?${params.toString()}` : "";
  return (await getJson<GraphEntityListResponse>(`/graph/entities${query}`))?.entities ?? [];
}

export async function fetchGraphEntity(
  key: string,
): Promise<GraphNeighborhoodResponse | null> {
  return getJson<GraphNeighborhoodResponse>(
    `/graph/entity?key=${encodeURIComponent(key)}`,
  );
}

export async function fetchGraphRelationships(
  type?: RelationshipType,
): Promise<GraphRelationship[]> {
  const query = type ? `?type=${type}` : "";
  return (
    (await getJson<GraphRelationshipListResponse>(`/graph/relationships${query}`))
      ?.relationships ?? []
  );
}

export async function fetchGraphRuns(): Promise<GraphBuildRun[]> {
  return (await getJson<GraphBuildRunListResponse>("/graph/build/runs"))?.runs ?? [];
}

export async function fetchGraphRun(id: string): Promise<GraphBuildRun | null> {
  return getJson<GraphBuildRun>(`/graph/build/runs/${id}`);
}

export async function fetchGraphRunEvents(runId: string): Promise<GraphBuildEvent[]> {
  return (
    (await getJson<GraphBuildEventListResponse>(`/graph/build/runs/${runId}/events`))
      ?.events ?? []
  );
}

export async function triggerGraphBuild(): Promise<MutationResult> {
  return postJson("/graph/build");
}

export async function createGraphEntity(
  input: EntityCreateRequest,
): Promise<MutationResult> {
  return postJson("/graph/entities", input);
}

export async function createGraphRelationship(
  input: RelationshipCreateRequest,
): Promise<MutationResult> {
  return postJson("/graph/relationships", input);
}

// --- Phase 4: Retrieval (search + embeddings) ---

export async function fetchSearch(
  query: string,
  mode: SearchMode = "hybrid",
): Promise<SearchResponse | null> {
  if (!query.trim()) return null;
  const params = new URLSearchParams({ q: query, mode });
  return getJson<SearchResponse>(`/search?${params.toString()}`);
}

export async function fetchEmbeddingStats(): Promise<EmbeddingStatsResponse | null> {
  return getJson<EmbeddingStatsResponse>("/embeddings/stats");
}

export async function fetchEmbeddingRuns(): Promise<EmbeddingRun[]> {
  return (await getJson<EmbeddingRunListResponse>("/embeddings/runs"))?.runs ?? [];
}

export async function fetchEmbeddingRun(id: string): Promise<EmbeddingRun | null> {
  return getJson<EmbeddingRun>(`/embeddings/runs/${id}`);
}

export async function fetchEmbeddingRunEvents(runId: string): Promise<EmbeddingEvent[]> {
  return (
    (await getJson<EmbeddingEventListResponse>(`/embeddings/runs/${runId}/events`))
      ?.events ?? []
  );
}

export async function triggerEmbedding(): Promise<MutationResult> {
  return postJson("/embeddings/runs");
}

// --- Phase 5: Trust ---

export async function fetchTrustSources(
  sourceType?: string,
): Promise<SourceTrustItem[]> {
  const query = sourceType ? `?source_type=${sourceType}` : "";
  return (await getJson<SourceListResponse>(`/trust/sources${query}`))?.sources ?? [];
}

export async function fetchFreshness(): Promise<FreshnessResponse | null> {
  return getJson<FreshnessResponse>("/trust/freshness");
}

export async function fetchTrustProfile(
  documentId: string,
): Promise<TrustProfileResponse | null> {
  return getJson<TrustProfileResponse>(`/trust/documents/${documentId}`);
}

// --- Phase 6: Engineering Assistant ---

export async function askAssistant(
  question: string,
  conversationId?: string,
): Promise<AskResponse | null> {
  return postJsonFor<AskResponse>("/assistant/ask", {
    question,
    conversation_id: conversationId ?? null,
  });
}

export async function fetchConversations(): Promise<ConversationSummary[]> {
  return (
    (await getJson<ConversationListResponse>("/assistant/conversations"))
      ?.conversations ?? []
  );
}

export async function fetchConversation(
  id: string,
): Promise<ConversationDetailResponse | null> {
  return getJson<ConversationDetailResponse>(`/assistant/conversations/${id}`);
}

// --- Phase 7: Engineering Intelligence ---

export async function fetchIntelligenceOverview(): Promise<OverviewResponse | null> {
  return getJson<OverviewResponse>("/intelligence/overview");
}

export async function fetchDependencyIntel(): Promise<DependencyReportResponse | null> {
  return getJson<DependencyReportResponse>("/intelligence/dependencies");
}

export async function fetchDebtIntel(): Promise<DebtReportResponse | null> {
  return getJson<DebtReportResponse>("/intelligence/debt");
}

export async function fetchIncidentIntel(): Promise<IncidentReportResponse | null> {
  return getJson<IncidentReportResponse>("/intelligence/incidents");
}

export async function fetchOwnershipIntel(): Promise<OwnershipReportResponse | null> {
  return getJson<OwnershipReportResponse>("/intelligence/ownership");
}

// --- Phase 8: Agent Layer ---

export async function fetchAgentCatalog(): Promise<AgentTypeInfo[]> {
  return (await getJson<AgentCatalogResponse>("/agents/catalog"))?.agents ?? [];
}

export async function runAgent(
  agentType: AgentType,
  target?: string,
): Promise<AgentRunDetailResponse | null> {
  return postJsonFor<AgentRunDetailResponse>("/agents/runs", {
    agent_type: agentType,
    target: target ?? null,
  });
}

export async function fetchAgentRuns(): Promise<AgentRunSummary[]> {
  return (await getJson<AgentRunListResponse>("/agents/runs"))?.runs ?? [];
}

export async function fetchAgentRun(
  id: string,
): Promise<AgentRunDetailResponse | null> {
  return getJson<AgentRunDetailResponse>(`/agents/runs/${id}`);
}
