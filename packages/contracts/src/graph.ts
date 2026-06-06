/** Knowledge-graph contracts — mirror apps/api/app/domain/graph.py + graph_entities.py. */
import type { SyncEventLevel, SyncStatus } from "./sync";

export type EntityKind =
  | "engineer"
  | "team"
  | "repository"
  | "service"
  | "api"
  | "incident"
  | "adr"
  | "document";

export type RelationshipType =
  | "owns"
  | "depends_on"
  | "modified"
  | "impacts"
  | "resolved";

export type GraphSource = "projection" | "manual";

export interface GraphBuildRun {
  id: string;
  status: SyncStatus;
  documents_seen: number;
  entity_count: number;
  relationship_count: number;
  error: string | null;
  started_at: string;
  finished_at: string | null;
}

export interface GraphBuildRunListResponse {
  runs: GraphBuildRun[];
}

export interface GraphBuildEvent {
  id: string;
  level: SyncEventLevel;
  message: string;
  created_at: string;
}

export interface GraphBuildEventListResponse {
  events: GraphBuildEvent[];
}

export interface GraphStatsResponse {
  total_entities: number;
  total_relationships: number;
  entities_by_kind: Record<string, number>;
  relationships_by_type: Record<string, number>;
}

export interface GraphEntity {
  kind: EntityKind;
  key: string;
  name: string;
  source: GraphSource;
  summary: string | null;
  url: string | null;
  category: string | null;
}

export interface GraphEntityListResponse {
  entities: GraphEntity[];
}

export interface GraphRelationship {
  type: RelationshipType;
  from_key: string;
  from_name: string | null;
  from_kind: EntityKind | null;
  to_key: string;
  to_name: string | null;
  to_kind: EntityKind | null;
}

export interface GraphRelationshipListResponse {
  relationships: GraphRelationship[];
}

export interface GraphNeighbor {
  type: RelationshipType;
  direction: "out" | "in";
  entity: GraphEntity;
}

export interface GraphNeighborhoodResponse {
  entity: GraphEntity;
  neighbors: GraphNeighbor[];
}

export interface EntityCreateRequest {
  kind: EntityKind;
  name: string;
  summary?: string | null;
  url?: string | null;
}

export interface RelationshipCreateRequest {
  type: RelationshipType;
  from_kind: EntityKind;
  from_name: string;
  to_kind: EntityKind;
  to_name: string;
}
