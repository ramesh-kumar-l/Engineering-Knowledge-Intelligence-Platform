# Glossary

Shared vocabulary for EKIP. Keep terms consistent across code, UI, and docs.

| Term | Definition |
|---|---|
| **EKIP** | Engineering Knowledge Intelligence Platform. |
| **Engineering Memory** | Stage 1: capturing and recalling engineering knowledge. |
| **Engineering Intelligence** | Stage 2: deriving insight and risk from knowledge. |
| **Engineering Cognition** | Stage 3: AI-native reasoning and action over knowledge. |
| **Memory Bank** | `.project-memory-bank/` — the project's source of truth. |
| **ADR** | Architecture Decision Record (Context · Options · Decision · Consequences). |
| **Connector** | An integration that ingests from a source (GitHub, Jira, etc.). |
| **Incremental sync** | Fetching only changes since the last sync. |
| **Chunk** | A processed, embeddable unit of a document or code artifact. |
| **Knowledge Graph** | Neo4j graph of entities and relationships. |
| **Entity** | A domain node (Engineer, Team, Service, Incident, ADR, Document, …). |
| **Relationship** | A graph edge (owns, depends_on, modified, impacts, resolved). |
| **Embedding** | Vector representation of a chunk, stored in Qdrant. |
| **Hybrid retrieval** | Combining keyword, vector, and graph retrieval with ranking. |
| **Trust score** | Composite measure of an answer's reliability. |
| **Confidence** | How reliable a specific answer is. |
| **Freshness** | How current the underlying knowledge is. |
| **Source attribution** | Linking an answer to its originating sources. |
| **Ownership** | The team/engineer accountable for an entity (graph `owns`). |
| **Evidence** | Supporting excerpts that back a claim. |
| **Tenant** | An isolated organization/customer scope. |
| **RBAC / ABAC** | Role- / attribute-based access control. |
| **Phase gate** | Mandatory STOP for approval at the end of a roadmap phase. |
| **Walking skeleton** | Thin end-to-end slice proving the whole stack works. |
