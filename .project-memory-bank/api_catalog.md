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
| `GET /health` | none | — | `{ "status": "ok", "version": str }` | core | planned |

> `GET /health` is the first endpoint of the Phase 0 code walking-skeleton — a
> liveness/readiness probe used to prove the stack end-to-end and by observability.

Phase 1+ will add connector, sync, processing, graph, retrieval, trust, assistant,
intelligence, and agent endpoints — each added here when implemented.
