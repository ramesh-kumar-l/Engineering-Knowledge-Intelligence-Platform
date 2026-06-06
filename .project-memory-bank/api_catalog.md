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

Phase 3+ will add graph, retrieval, trust, assistant, intelligence, and agent
endpoints — each added here when implemented.
