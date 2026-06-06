# API Catalog

Authoritative list of EKIP HTTP APIs. Populated as endpoints are implemented. Backend
is FastAPI (ADR-0002); OpenAPI is auto-generated and should stay consistent with this
catalog.

## Entry format

| Field | Meaning |
|---|---|
| Method + Path | HTTP verb and route |
| Auth | Required auth/role (RBAC) |
| Request | Body/query schema |
| Response | Response schema |
| Owning module | Backend module/layer |
| Status | planned · implemented |

---

## Endpoints

| Method + Path | Auth | Request | Response | Owning module | Status |
|---|---|---|---|---|---|
| `GET /health` | none | — | `HealthResponse` `{ status, version }` | api/routes/health | implemented |
| `GET /health/ready` | none | — | `ReadinessResponse` `{ status, version, dependencies[] }` | api/routes/health | implemented |
| `GET /connectors/catalog` | viewer | — | `ConnectorCatalogResponse` | api/routes/connectors | implemented |
| `GET /connectors` | viewer | — | `ConnectorListResponse` | api/routes/connectors | implemented |
| `POST /connectors` | editor | `ConnectorCreate` | `ConnectorOut` (201) | api/routes/connectors | implemented |
| `GET /connectors/{id}` | viewer | — | `ConnectorOut` | api/routes/connectors | implemented |
| `POST /connectors/{id}/sync` | editor | — | `SyncRunOut` | api/routes/connectors | implemented |
| `GET /sync/runs` | viewer | `?connector_id&limit` | `SyncRunListResponse` | api/routes/sync | implemented |
| `GET /sync/runs/{id}` | viewer | — | `SyncRunOut` | api/routes/sync | implemented |
| `GET /sync/runs/{id}/events` | viewer | — | `SyncEventListResponse` | api/routes/sync | implemented |
| `GET /documents` | viewer | `?connector_id&limit&offset` | `DocumentListResponse` | api/routes/documents | implemented |
| `POST /processing/runs` | editor | `ProcessingTriggerRequest` (optional) | `ProcessingRunOut` | api/routes/processing | implemented |
| `GET /processing/runs` | viewer | `?limit` | `ProcessingRunListResponse` | api/routes/processing | implemented |
| `GET /processing/runs/{id}` | viewer | — | `ProcessingRunOut` | api/routes/processing | implemented |
| `GET /processing/runs/{id}/events` | viewer | — | `ProcessingEventListResponse` | api/routes/processing | implemented |
| `GET /processing/stats` | viewer | — | `ChunkStatsResponse` | api/routes/processing | implemented |
| `GET /processing/documents` | viewer | `?limit&offset` | `ProcessedDocumentListResponse` | api/routes/processing | implemented |
| `GET /processing/documents/{document_id}` | viewer | — | `DocumentProcessingDetail` | api/routes/processing | implemented |
| `POST /graph/build` | editor | `GraphBuildTriggerRequest` (optional) | `GraphBuildRunOut` | api/routes/graph | implemented |
| `GET /graph/stats` | viewer | — | `GraphStatsResponse` | api/routes/graph | implemented |
| `GET /graph/build/runs` | viewer | `?limit` | `GraphBuildRunListResponse` | api/routes/graph | implemented |
| `GET /graph/build/runs/{id}` | viewer | — | `GraphBuildRunOut` | api/routes/graph | implemented |
| `GET /graph/build/runs/{id}/events` | viewer | — | `GraphBuildEventListResponse` | api/routes/graph | implemented |
| `GET /graph/entities` | viewer | `?kind&search&limit&offset` | `GraphEntityListResponse` | api/routes/graph_entities | implemented |
| `GET /graph/entity` | viewer | `?key` | `GraphNeighborhoodResponse` | api/routes/graph_entities | implemented |
| `GET /graph/relationships` | viewer | `?type&limit` | `GraphRelationshipListResponse` | api/routes/graph_entities | implemented |
| `POST /graph/entities` | editor | `EntityCreateRequest` | `GraphEntityOut` | api/routes/graph_entities | implemented |
| `POST /graph/relationships` | editor | `RelationshipCreateRequest` | `GraphRelationshipOut` | api/routes/graph_entities | implemented |
| `POST /embeddings/runs` | editor | `EmbeddingTriggerRequest` (optional) | `EmbeddingRunOut` | api/routes/embeddings | implemented |
| `GET /embeddings/stats` | viewer | — | `EmbeddingStatsResponse` | api/routes/embeddings | implemented |
| `GET /embeddings/runs` | viewer | `?limit` | `EmbeddingRunListResponse` | api/routes/embeddings | implemented |
| `GET /embeddings/runs/{id}` | viewer | — | `EmbeddingRunOut` | api/routes/embeddings | implemented |
| `GET /embeddings/runs/{id}/events` | viewer | — | `EmbeddingEventListResponse` | api/routes/embeddings | implemented |
| `GET /search` | viewer | `?q&mode&limit` | `SearchResponse` | api/routes/search | implemented |
| `GET /trust/sources` | viewer | `?source_type&limit&offset` | `SourceListResponse` | api/routes/trust | implemented |
| `GET /trust/freshness` | viewer | — | `FreshnessResponse` | api/routes/trust | implemented |
| `GET /trust/documents/{id}` | viewer | — | `TrustProfileResponse` | api/routes/trust | implemented |

> `GET /health` is liveness (process up, no I/O). `GET /health/ready` is readiness:
> it aggregates PostgreSQL/Neo4j/Qdrant health and returns **503** when any store is
> degraded so orchestrators hold traffic. Schemas live in `apps/api/app/domain/` and
> are mirrored as TypeScript in `packages/contracts` (R2 mitigation).

> **Auth (ADR-0008).** All non-health routes require a `Bearer` JWT (claims: `sub`,
> `tenant_id`, `role`) enforced by `require_role`. Outside production a dev header
> fallback (`X-Tenant-Id` / `X-Role`) is accepted. Every response is tenant-scoped to
> the principal; mutations write an `AuditEvent`.

> **Processing (Phase 2).** `POST /processing/runs` executes the pipeline
> synchronously (ADR-0009) over documents needing (re)processing and records a
> `ProcessingRun` + events + an `AuditEvent`. `GET /processing/stats` powers Chunk
> Statistics; `GET /processing/documents{,/{id}}` power the Parsing Explorer.

> **Knowledge Graph (Phase 3).** `POST /graph/build` projects the tenant's connectors +
> documents into the graph store (Neo4j; ADR-0012/0013) synchronously and records a
> `GraphBuildRun` + events + an `AuditEvent`. `GET /graph/entities`, `/graph/entity` and
> `/graph/relationships` power the Knowledge/Service/Team explorers and Dependency Graph;
> `POST /graph/entities` and `/graph/relationships` curate Services + `depends_on` edges
> (audited). `key` is passed as a query param because entity keys contain `/`.

> **Retrieval (Phase 4).** `POST /embeddings/runs` embeds the tenant's processed chunks
> into the vector store (Qdrant; ADR-0014/0015) synchronously and records an
> `EmbeddingRun` + events + an `AuditEvent`; staleness (`DocumentEmbeddingState`) skips
> unchanged documents unless `force`. `GET /embeddings/stats` powers the Search Explorer.
> `GET /search?q=&mode=` runs hybrid retrieval — keyword + vector over chunks fused by
> reciprocal rank (ADR-0016), plus a knowledge-graph entity facet; `mode` is
> `keyword`/`vector`/`hybrid` (default).

> **Trust (Phase 5).** Read-only and tenant-scoped; trust is computed on read
> (ADR-0017), so there is no run/trigger. `GET /trust/documents/{id}` returns the full
> profile — confidence (with a per-signal contribution breakdown), freshness band,
> source provenance, graph-attributed owners (ADR-0018) and supporting excerpts.
> `GET /trust/sources` powers the Source Explorer; `GET /trust/freshness` powers the
> Freshness Dashboard (corpus distribution + the documents most needing attention).

Phase 6+ will add assistant, intelligence, and agent endpoints — each added here when
implemented.
