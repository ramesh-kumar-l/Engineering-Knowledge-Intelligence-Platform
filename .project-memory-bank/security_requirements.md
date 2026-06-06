# Security Requirements

Security is first-class and **cannot be postponed** (ADR-0006). These are mandatory
requirements implemented progressively in code increments and enforced as acceptance
criteria.

## Mandatory controls

| Control | Requirement | Phase introduced |
|---|---|---|
| **RBAC** | Role-based access control on all APIs | 0 (code) scaffold → enforced 1+ |
| **ABAC-ready** | Architecture supports attribute-based policies later | 0 (design) |
| **OAuth / SSO** | Federated auth for users | 1 |
| **Audit logging** | Immutable record of sensitive actions | 0 (code) scaffold |
| **Encryption in transit** | TLS everywhere | 0 (code) |
| **Encryption at rest** | Datastores + secrets encrypted | 0 (code) infra |
| **Tenant isolation** | Every entity scoped to a tenant; no cross-tenant leakage | 0 (design) → enforced 1+ |
| **Secrets management** | No secrets in repo; injected via env/secret store | 0 (code) |

## Principles

- **Least privilege** by default for users, services, and connectors.
- **Defense in depth** — auth at the edge *and* tenant checks in the data layer.
- **Connector credentials** stored encrypted; scoped to the minimum required access.
- **Auditability** — security-relevant events are logged and tamper-evident.
- **Privacy** — ingested knowledge may be sensitive; handle per tenant policy.

## Verification

- Security checks in CI (dependency scanning, secret scanning).
- Tenant-isolation tests are integration-level and required (see
  [`testing_strategy.md`](testing_strategy.md)).
- Use `/security-review` on changes that touch auth, tenancy, or data access.

Cross-references: [`architecture_decisions.md`](architecture_decisions.md) (ADR-0006),
[`domain_model.md`](domain_model.md) (tenant scoping).
