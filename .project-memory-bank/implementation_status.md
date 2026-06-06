# Implementation Status

> **Read this first.** Live state of the project. Updated after every task.

**Last updated:** 2026-06-06

## Current phase

**Phase 1 — Knowledge Ingestion Layer.** Complete and verified; **at the phase gate**
awaiting approval to start Phase 2. Phase 0 is done.

## Completed work

### Phase 0 — Project Foundation ✅
Memory bank + ADRs (0001–0007); code walking-skeleton (FastAPI health/readiness over
PG/Neo4j/Qdrant, Next.js dark App Shell + Overview, shared contracts, docker-compose,
CI, security scaffolding). All gates green.

### Phase 1 — Knowledge Ingestion Layer ✅

- **Persistence (PostgreSQL, system of record):** ORM models `Connector`, `SyncRun`,
  `SyncEvent`, `Document`, `AuditEvent` (`app/models/`), all tenant-scoped; portable
  types so the same models run on SQLite for tests. Async session factory on
  `PostgresStore`; dev schema bootstrap in lifespan (`auto_create_schema`).
- **Repository layer (`app/repositories/`):** tenant-scoped data access for
  connectors, documents, sync runs/events, audit.
- **Connector framework (`app/connectors/`):** `Connector` protocol + `RawDocument`/
  `FetchResult`, a 6-source **catalog**, and a **registry** that builds a live
  connector from stored config. **GitHub connector** implemented (issues, incremental
  via `since`, PR-skip, pagination cap). Other 5 sources are catalog entries (planned).
- **Sync engine (`app/services/sync_service.py`):** drives a connector, reconciles via
  SHA-256 content hash (created/updated/unchanged/deleted), records counters + log
  events, advances the cursor, and captures failures on the run (ADR-0009).
- **Services:** `ConnectorService` (catalog validation + secret encryption),
  `AuditService` (persisted audit).
- **APIs (`app/api/routes/`):** connectors (catalog/list/create/get/sync), sync
  (runs/run/events), documents — all RBAC-enforced + tenant-scoped (api_catalog.md).
- **Security (ADR-0008):** JWT bearer verification is the production boundary
  (`get_principal`); dev header fallback gated to non-production; connector secrets
  encrypted at rest (Fernet `SecretBox`); secrets write-only over the API;
  **PostgreSQL-backed audit events** replace the Phase 0 log-only scaffold.
- **Web (`apps/web`):** Connector Catalog, Connector Details, Sync Dashboard, Sync
  Logs — server components reading the typed API client, mutations via server actions
  (create connector, run sync); active-route sidebar nav; reusable `Badge`.
- **Contracts (`packages/contracts`):** TS mirrors for connector/sync/document schemas.
- **Tests:** 30 passing — crypto, GitHub connector (httpx mock), sync engine + change
  tracking (SQLite), connector/sync/document routes, RBAC + tenant isolation, JWT auth.
  Gates green: **ruff · mypy strict (50 files) · pytest 30/30**; web **lint · tsc ·
  next build**.

## Current architecture state

End-to-end ingestion works: UI → API (JWT/RBAC, tenant-scoped) → SyncService →
GitHub connector → PostgreSQL documents + sync runs/events + audit. Modular monolith;
the sync path is queue-agnostic for a future worker.

## Risks

- **R1 — Operational complexity (3 datastores):** mitigated (registry abstraction,
  readiness per store). Phase 1 uses PostgreSQL only; Neo4j/Qdrant unused until 2/3.
- **R2 — Two-language stack:** mitigated (shared `packages/contracts`; parity by review).

## Technical debt

- **Single implemented connector (GitHub).** GitLab/Jira/Confluence/Slack/Notion are
  catalog entries only; add factories in `app/connectors/registry.py`.
- **Synchronous sync execution (ADR-0009).** No durable background worker/queue yet;
  large backfills are bounded per request.
- **No Alembic migrations yet.** Schema is created via `create_all` (dev). Add Alembic
  before first production deploy. Tests use SQLite `create_all`.
- **Auth completeness.** HS256 with a shared secret; JWKS/RS256 rotation, token
  issuance/login UI, and full SSO wiring are pending. Default dev secrets
  (`EKIP_JWT_SECRET`, `EKIP_SECRET_KEY`) **must** be overridden via env in prod.
- **Deletion detection** relies on connector-provided `deleted_ids` (GitHub issues are
  closed, not deleted) — full reconciliation deferred.

## Pending decisions

- OAuth/OIDC provider for production token issuance + login UI (Phase 1 follow-up).
- Background job runner (Celery/Arq/RQ) when sync volume warrants (revisits ADR-0009).
- Embedding model + provider for Qdrant (Phase 2/4).

## Recommended next action

Obtain phase-gate approval, then begin **Phase 2 — Knowledge Processing Layer**
(parse, chunk, classify, enrich, summarize) over the ingested `Document`s, driven by
the ADRs, `coding_standards.md`, and `testing_strategy.md`.

> **Phase gate:** Phase 1 is complete and verified; **STOP for approval** before
> Phase 2.
