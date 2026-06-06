# Domain Model

The core domain of EKIP. Entities live in PostgreSQL (system of record) and/or Neo4j
(knowledge graph). The graph is the authoritative source for relationships and
traversal; PostgreSQL holds operational/relational state.

## Core entities

| Entity | Description | PG | Neo4j |
|---|---|---|---|
| **Engineer** | A person who contributes to systems | ✓ (user/identity) | ✓ |
| **Team** | A group that owns services/repos | ✓ | ✓ |
| **Repository** | A source code repository | ✓ | ✓ |
| **Service** | A deployable/running service | ✓ | ✓ |
| **API** | An interface exposed by a service | — | ✓ |
| **Incident** | An operational failure event | ✓ | ✓ |
| **ADR** | An architecture decision record | ✓ | ✓ |
| **Document** | A knowledge artifact (doc, page, message thread) | ✓ | ✓ |

Operational entities (PostgreSQL only): `Tenant`, `User`, `Role`, `Connector`,
`SyncJob`, `ProcessingJob`, `Chunk`, `AuditEvent`, `TrustRecord`.

## Relationships (Neo4j)

| Relationship | From → To | Meaning |
|---|---|---|
| `owns` | Team/Engineer → Service/Repository/API | Ownership |
| `depends_on` | Service/Repository → Service/API | Dependency |
| `modified` | Engineer → Repository/Service/Document | Authored a change |
| `impacts` | Incident → Service/Repository | Blast radius |
| `resolved` | Engineer/Team → Incident | Resolution |

## Notes

- Embeddings of `Chunk`s (derived from `Document`s and code) live in **Qdrant**, keyed
  back to PostgreSQL/Neo4j IDs for attribution.
- Every entity carries provenance (source connector, last-synced timestamp) to power
  the [`trust_framework.md`](trust_framework.md) (freshness, source attribution).
- Multi-tenancy: every entity is scoped to a `Tenant` (ADR-0006).

See [`system_architecture.md`](system_architecture.md) for store mapping and
[`glossary.md`](glossary.md) for term definitions.
