# Active Context

> Compressed "save state" for resuming work fast. Pairs with
> [`implementation_status.md`](implementation_status.md) (full status). Update before
> ending any major feature.

**Last updated:** 2026-06-06

## Where we are

Phase 1 — Knowledge Ingestion is **complete and verified**, sitting at the **phase
gate** awaiting approval to start Phase 2. End-to-end ingestion runs: UI → API
(JWT/RBAC, tenant-scoped) → SyncService → GitHub connector → PostgreSQL.

## What just happened (this increment)

Built the ingestion layer: ORM models + repositories (`app/models`, `app/repositories`),
connector framework + GitHub connector (`app/connectors`), sync engine + services
(`app/services`), connector/sync/document APIs (`app/api/routes`), JWT auth + Fernet
secret encryption + persisted audit (ADR-0008/0009), and the four ingestion screens
(`apps/web/app/connectors`, `apps/web/app/sync`). Added ADR-0008 and ADR-0009.

Gates: API `ruff` clean · `mypy app` clean (50 files) · `pytest` 30/30. Web
`lint` · `typecheck` · `build` all green.

## How to run it

```bash
docker compose -f infra/docker-compose.yml up -d          # PG + Neo4j + Qdrant
cd apps/api && uvicorn app.main:app --reload              # API on :8000 (auto-creates schema in dev)
cd apps/web && npm run dev                                # Web on :3000
```

Dev auth: the web client sends `X-Tenant-Id`/`X-Role` (editor) headers. Set
`EKIP_TENANT_ID`/`EKIP_ROLE` to change. In production set `EKIP_JWT_SECRET`,
`EKIP_SECRET_KEY`, `EKIP_DEV_AUTH_ENABLED=false` and send real `Bearer` JWTs.

## Active decisions / constraints to remember

- JWT bearer is the prod auth boundary; dev header fallback only when not production
  (ADR-0008). Connector secrets encrypted at rest; never returned over the API.
- Sync runs synchronously in the trigger request (ADR-0009); SyncService is
  queue-agnostic for a future worker.
- Only the GitHub connector is implemented; others are catalog entries.
- No Alembic yet — `create_all` for dev, SQLite for tests. Add migrations before prod.
- Keep files < 300 lines; one concern per file. Python schemas authoritative; TS
  `packages/contracts` mirror them.

## Next step (after gate approval)

Phase 2 — Knowledge Processing Layer: parse/chunk/classify/enrich/summarize the
ingested `Document`s (PostgreSQL + Qdrant). See [`roadmap.md`](roadmap.md) Phase 2.
