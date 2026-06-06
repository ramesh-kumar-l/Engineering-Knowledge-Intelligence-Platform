/**
 * EKIP shared API contracts.
 *
 * These TypeScript types MUST stay in sync with the Pydantic schemas in
 * `apps/api/app/domain/schemas.py`. Keeping one shared definition is the R2
 * mitigation from implementation_status.md (preventing Python/TS contract drift).
 */
export type * from "./health";
export type * from "./connectors";
export type * from "./sync";
export type * from "./documents";
export type * from "./processing";
export type * from "./chunks";
export type * from "./graph";
export type * from "./embedding";
export type * from "./search";
export type * from "./trust";
export type * from "./assistant";
