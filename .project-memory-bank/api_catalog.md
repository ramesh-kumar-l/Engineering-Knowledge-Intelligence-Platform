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

> `GET /health` is liveness (process up, no I/O). `GET /health/ready` is readiness:
> it aggregates PostgreSQL/Neo4j/Qdrant health and returns **503** when any store is
> degraded so orchestrators hold traffic. Schemas live in `apps/api/app/domain/
> schemas.py` and are mirrored as TypeScript in `packages/contracts` (R2 mitigation).

Phase 1+ will add connector, sync, processing, graph, retrieval, trust, assistant,
intelligence, and agent endpoints — each added here when implemented.
