# infra/

Local development infrastructure and CI/CD config (ADR-0005).

## Datastores (local dev)

`docker-compose.yml` runs the three stores the API depends on (ADR-0004):

| Service | Port(s) | Purpose |
|---|---|---|
| PostgreSQL | 5432 | System of record |
| Neo4j | 7474 (browser), 7687 (bolt) | Knowledge graph |
| Qdrant | 6333 (http), 6334 (grpc) | Vector store |

```bash
docker compose -f infra/docker-compose.yml up -d     # start
docker compose -f infra/docker-compose.yml ps        # status
docker compose -f infra/docker-compose.yml down      # stop (keeps volumes)
```

With these up, the API's `GET /health/ready` reports all three as healthy.

> Credentials in the compose file are **dev-only**. Staging/production use a secret
> store, not committed files (`security_requirements.md`).

## CI

Pipelines live in [`.github/workflows/`](../.github/workflows/). `ci.yml` runs the
backend (ruff + mypy + pytest) and frontend (lint + typecheck + build) gates on every
push and PR.
