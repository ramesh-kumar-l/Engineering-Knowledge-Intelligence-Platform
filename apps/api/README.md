# EKIP API

FastAPI backend for the Engineering Knowledge Intelligence Platform (ADR-0002).
Modular monolith; internal modules map to the roadmap layers
(see [`system_architecture.md`](../../.project-memory-bank/system_architecture.md)).

## Layout

```
app/
├── core/            # config, logging, security (RBAC), datastore clients
│   └── db/          # postgres / neo4j / qdrant clients + registry
├── domain/          # Pydantic schemas (the typed API contract)
├── middleware/      # request correlation, audit logging
├── api/             # routers + route-level deps
│   └── routes/      # one file per concern (health, …)
└── main.py          # app factory + lifespan (composition root)
```

## Endpoints

| Method + Path | Purpose |
|---|---|
| `GET /health` | Liveness — process is up (no I/O). |
| `GET /health/ready` | Readiness — checks Postgres + Neo4j + Qdrant; 503 if degraded. |

OpenAPI docs at `/docs` when running.

## Develop

```bash
python -m venv .venv
.venv/Scripts/activate        # Windows; use source .venv/bin/activate on *nix
pip install -e ".[dev]"
cp .env.example .env          # configure datastore connections

uvicorn app.main:app --reload # serve on http://localhost:8000
```

Datastores for `GET /health/ready`: run them via
[`infra/docker-compose.yml`](../../infra/docker-compose.yml).

## Quality gates

```bash
ruff check .      # lint
mypy app          # type check (strict)
pytest -q         # tests (no live datastores required)
```

All three run in CI on every PR ([`.github/workflows/ci.yml`](../../.github/workflows/ci.yml)).
