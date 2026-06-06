/** Sync contracts — mirror apps/api/app/domain/sync.py. */
export type SyncStatus = "running" | "succeeded" | "failed";

export type SyncEventLevel = "info" | "warning" | "error";

export interface SyncRun {
  id: string;
  connector_id: string;
  status: SyncStatus;
  documents_seen: number;
  created_count: number;
  updated_count: number;
  unchanged_count: number;
  deleted_count: number;
  error: string | null;
  started_at: string;
  finished_at: string | null;
}

export interface SyncRunListResponse {
  runs: SyncRun[];
}

export interface SyncEvent {
  id: string;
  level: SyncEventLevel;
  message: string;
  created_at: string;
}

export interface SyncEventListResponse {
  events: SyncEvent[];
}
