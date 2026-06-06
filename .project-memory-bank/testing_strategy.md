# Testing Strategy

> No feature is complete without tests.

## Required test levels

| Level | Scope | Tooling (intended) |
|---|---|---|
| **Unit** | Pure functions, domain logic, components | pytest · Vitest/RTL |
| **Integration** | Service + real datastores (PG/Neo4j/Qdrant) | pytest + docker-compose |
| **Contract** | API request/response schemas (FE ↔ BE) | schema/contract tests |
| **End-to-end** | Critical user journeys through the UI | Playwright |

## Practices

- **Goal-driven:** for bugs, write a failing test that reproduces it, then fix.
- For features, define success criteria as tests before implementation where practical.
- Tests run in CI on every PR; merges blocked on failure.
- Integration tests spin up ephemeral PG/Neo4j/Qdrant via `infra/` docker-compose.

## Quality metrics (tracked as the platform matures)

Tie to [`trust_framework.md`](trust_framework.md) and observability:

- Retrieval quality
- Agent accuracy
- Hallucination rate
- Knowledge coverage
- Sync success rate
- Query latency

These graduate from "tracked" to "gated" as the relevant phases land.
