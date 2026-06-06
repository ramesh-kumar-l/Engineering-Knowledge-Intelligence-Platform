# Implementation Status

> **Read this first.** Live state of the project. Updated after every task.

**Last updated:** 2026-06-06

## Current phase

**Phase 0 — Project Foundation.** Both increments complete; **at the phase gate**
awaiting approval to start Phase 1.

## Completed work

### Docs increment ✅
- Memory Bank (`.project-memory-bank/`) established as the source of truth (16 files).
- Foundational ADRs ([`architecture_decisions.md`](architecture_decisions.md)):
  ADR-0001…0006 (memory-bank-first, FastAPI, Next.js, PG+Neo4j+Qdrant, monorepo,
  security baseline).

### Code walking-skeleton ✅
Monorepo per ADR-0005: `apps/api`, `apps/web`, `packages/`, `infra/`, `.github/`.

- **API (`apps/api`, FastAPI — ADR-0002):**
  - `core/`: env-based `Settings` (pydantic-settings), JSON structured logging with
    request-id correlation, RBAC scaffolding (`Role`, `Principal`, `require_role`).
  - `core/db/`: `PostgresStore`, `Neo4jStore`, `QdrantStore` (each `connect`/`close`/
    `health_check`) behind a `DataStore` protocol + `DataStores` registry (R1 store
    abstraction).
  - `api/routes/health.py`: `GET /health` (liveness) and `GET /health/ready`
    (readiness; 503 when any store degraded).
  - `middleware/`: request correlation + audit-log scaffold (mutations).
  - `main.py`: app factory + lifespan wiring; CORS.
  - Tests: 9 passing (health liveness, readiness 200/503, request-id, RBAC hierarchy).
  - Gates green: **ruff clean · mypy strict clean (22 files) · pytest 9/9**.
- **Web (`apps/web`, Next.js App Router — ADR-0003):** dark-mode-first App Shell
  (sidebar + header), Overview screen (server component) that fetches
  `GET /health/ready` and renders backend + datastore health via a status badge
  (trust-UX precursor); Tailwind tokenized theme; typed API client using shared
  contracts. Gates green: **eslint clean · tsc strict clean · next build succeeds**.
- **`packages/contracts`:** type-only TS mirror of the API Pydantic schemas (R2
  mitigation), consumed via tsconfig path alias + `transpilePackages`.
- **`infra/docker-compose.yml`:** PostgreSQL 16 + Neo4j 5 + Qdrant for local dev.
- **CI (`.github/workflows/ci.yml`):** api gate, web gate, and security scanning
  (gitleaks secret scan + dependency review); least-privilege token.
- **ADR-0007:** monorepo tooling (per-app native tooling; type-only shared package).
- **Security posture (scaffold, ADR-0006):** RBAC roles + `require_role`, tenant-scoped
  `Principal`, audit middleware, request correlation, secrets via env (`.env.example`,
  never committed), non-root API container, CI secret/dependency scanning.

## Current architecture state

Runnable thin slice end-to-end: web Overview → API `/health/ready` → 3 datastore
probes. Modular monolith; internal modules map to roadmap layers
([`system_architecture.md`](system_architecture.md)). No domain entities/connectors
yet (Phase 1+).

## Risks

- **R1 — Operational complexity (ADR-0004):** three datastores. *Mitigation in place:*
  docker-compose for local dev; per-store client + registry abstraction; readiness
  reports each store independently.
- **R2 — Two-language stack:** *Mitigation in place:* shared type-only
  `packages/contracts` mirrors the Pydantic schemas; parity kept by review.

## Technical debt

- **DEV-only auth resolver:** `get_principal` derives identity from request headers to
  exercise RBAC before OAuth/SSO. **Not a security boundary**; replace in Phase 1.
- **Audit log is log-only:** structured audit lines, not yet a persisted/tamper-evident
  store (PostgreSQL-backed audit events land in Phase 1).
- **Contract parity is by convention** (no codegen yet) — acceptable at current size.

## Pending decisions

- Auth provider for OAuth/SSO (Phase 1).
- Embedding model + provider for Qdrant (Phase 2/4).
- Whether to introduce Turborepo/uv workspaces if build coordination grows (revisits
  ADR-0007).

## Recommended next action

Obtain phase-gate approval, then begin **Phase 1 — Knowledge Ingestion Layer**
(connectors, incremental sync, metadata, change tracking + Connector/Sync UI), driven
by the ADRs, [`coding_standards.md`](coding_standards.md), and
[`testing_strategy.md`](testing_strategy.md).

> **Phase gate:** Phase 0 is code-complete and verified; **STOP for approval** before
> Phase 1.
