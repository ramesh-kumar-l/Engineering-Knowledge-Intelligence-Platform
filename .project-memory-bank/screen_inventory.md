# Screen Inventory

Every screen serves a documented journey ([`user_journeys.md`](user_journeys.md)).
Status: ⬜ planned · 🟡 in progress · ✅ shipped. All screens are currently **planned**
(no UI code yet). Design language: [`ui_design_system.md`](ui_design_system.md).

| Screen | Phase | Serves journey | Status |
|---|---|---|---|
| App Shell (nav, theme, layout) | 0 (code) | foundation for all | ⬜ |
| Connector Catalog | 1 | J7 | ⬜ |
| Connector Details | 1 | J7 | ⬜ |
| Sync Dashboard | 1 | J7 | ⬜ |
| Sync Logs | 1 | J7 | ⬜ |
| Processing Dashboard | 2 | (ops support for J1–J6) | ⬜ |
| Chunk Statistics | 2 | (ops) | ⬜ |
| Parsing Explorer | 2 | (ops) | ⬜ |
| Processing Jobs | 2 | (ops) | ⬜ |
| Knowledge Explorer | 3 | J1, J3, J6 | ⬜ |
| Service Explorer | 3 | J1, J2 | ⬜ |
| Team Explorer | 3 | J2, J6 | ⬜ |
| Dependency Graph | 3 | J3, J5 | ⬜ |
| Global Search | 4 | J1, J2 | ⬜ |
| Advanced Search | 4 | J1, J2 | ⬜ |
| Search Explorer | 4 | J1 | ⬜ |
| Trust Inspector | 5 | J1, J4 (cross-cutting) | ⬜ |
| Source Explorer | 5 | J4 | ⬜ |
| Freshness Dashboard | 5 | J5 | ⬜ |
| Assistant Workspace | 6 | J1, J2, J3, J4, J6 | ⬜ |
| Conversation History | 6 | (assistant support) | ⬜ |
| Evidence Viewer | 6 | J3, J4 | ⬜ |
| Intelligence Dashboard | 7 | J5 | ⬜ |
| Technical Debt Dashboard | 7 | J5 | ⬜ |
| Dependency Risk Dashboard | 7 | J5 | ⬜ |
| Agent Workspace | 8 | (agent ops) | ⬜ |
| Agent Execution Viewer | 8 | (agent ops) | ⬜ |
| Agent Audit Trail | 8 | (agent ops, audit) | ⬜ |

> Rule: do not add a screen here without a journey it serves. "ops" screens support
> operating the platform itself and trace back to keeping journeys reliable.
