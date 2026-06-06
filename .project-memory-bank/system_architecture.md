# System Architecture

High-level architecture for EKIP. This document is forward-looking: it describes the
target structure that the phased roadmap builds toward. No code exists yet.

## Layered pipeline

Knowledge flows through layers that map to the roadmap phases:

```
            ┌──────────────────────────────────────────────────────────┐
 Sources →  │ Ingestion → Processing → Knowledge Graph → Retrieval →    │
 (GitHub,   │ Trust → Assistant → Intelligence → Agents                 │
  Jira,     └──────────────────────────────────────────────────────────┘
  Slack…)                       ▲ visible trust on every answer ▲
```

| Layer | Phase | Responsibility | Primary store |
|---|---|---|---|
| Ingestion | 1 | Connectors, incremental sync, metadata, change tracking | PostgreSQL |
| Processing | 2 | Parse, chunk, classify, enrich, summarize | PostgreSQL + Qdrant |
| Knowledge Graph | 3 | Entities + relationships, traversal | Neo4j |
| Retrieval | 4 | Keyword + vector + graph retrieval, hybrid ranking | Qdrant + Neo4j + PG |
| Trust | 5 | Confidence, freshness, attribution, ownership validation | PostgreSQL |
| Assistant | 6 | Q&A over knowledge with evidence | all |
| Intelligence | 7 | Dependency/debt/incident/ownership insight | all |
| Agents | 8 | Incident/onboarding/architecture/maintenance agents | all |

## Datastore roles (ADR-0004)

- **PostgreSQL** — system of record: tenants, users, roles, connectors, sync jobs,
  processing jobs, audit log, trust metadata.
- **Neo4j** — knowledge graph: `Engineer`, `Team`, `Repository`, `Service`, `API`,
  `Incident`, `ADR`, `Document` and relationships `owns`, `depends_on`, `modified`,
  `impacts`, `resolved`. Powers graph retrieval and dependency views.
- **Qdrant** — vector embeddings of chunks; semantic/vector retrieval.

See [`domain_model.md`](domain_model.md) for entity/relationship detail.

## Target monorepo layout (ADR-0005)

```
.
├── apps/
│   ├── api/                 # FastAPI services (ASGI / uvicorn)
│   │   ├── app/
│   │   │   ├── core/        # config, security, db clients, telemetry
│   │   │   ├── domain/      # entities, schemas (Pydantic)
│   │   │   ├── connectors/  # ingestion (Phase 1+)
│   │   │   ├── api/         # routers (e.g. /health first)
│   │   │   └── main.py
│   │   └── tests/
│   └── web/                 # Next.js (App Router) + Tailwind + shadcn/ui
│       ├── app/
│       ├── components/
│       └── lib/
├── packages/                # shared types, API clients, design tokens
├── infra/                   # docker-compose (PG/Neo4j/Qdrant), CI/CD, IaC
└── .project-memory-bank/    # source of truth
```

## Cross-cutting concerns

- **Security** — RBAC + tenant isolation enforced at the API boundary (ADR-0006,
  [`security_requirements.md`](security_requirements.md)).
- **Observability** — metrics, logs, traces, health checks; OpenTelemetry preferred.
- **Configuration** — environment-based; secrets never committed.

## Service boundaries

The backend starts as a modular monolith (`apps/api`) with clear internal module
boundaries per layer, so services can be extracted later without rewrites. This favors
reliability and maintainability over premature microservice complexity.
