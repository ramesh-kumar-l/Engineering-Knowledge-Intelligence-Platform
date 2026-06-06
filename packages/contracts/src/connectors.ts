/**
 * Connector contracts — mirror apps/api/app/domain/connectors.py.
 * Secrets are write-only: never returned, only `has_secret` is exposed.
 */
export type SourceType =
  | "github"
  | "gitlab"
  | "jira"
  | "confluence"
  | "slack"
  | "notion";

export type ConnectorStatus = "active" | "paused" | "error";

export interface ConfigFieldInfo {
  key: string;
  label: string;
  required: boolean;
}

export interface SourceTypeInfo {
  source_type: SourceType;
  label: string;
  description: string;
  implemented: boolean;
  config_fields: ConfigFieldInfo[];
  secret_label: string | null;
}

export interface ConnectorCatalogResponse {
  sources: SourceTypeInfo[];
}

export interface ConnectorCreate {
  source_type: SourceType;
  name: string;
  config: Record<string, unknown>;
  secret?: string | null;
}

export interface Connector {
  id: string;
  source_type: SourceType;
  name: string;
  status: ConnectorStatus;
  config: Record<string, unknown>;
  has_secret: boolean;
  cursor: string | null;
  last_synced_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface ConnectorListResponse {
  connectors: Connector[];
}
