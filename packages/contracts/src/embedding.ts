/** Embedding (index) contracts — mirror apps/api/app/domain/embedding.py. */
import type { SyncEventLevel, SyncStatus } from "./sync";

export interface EmbeddingRun {
  id: string;
  status: SyncStatus;
  documents_seen: number;
  documents_embedded: number;
  documents_skipped: number;
  chunk_count: number;
  failed_count: number;
  error: string | null;
  started_at: string;
  finished_at: string | null;
}

export interface EmbeddingRunListResponse {
  runs: EmbeddingRun[];
}

export interface EmbeddingEvent {
  id: string;
  level: SyncEventLevel;
  message: string;
  created_at: string;
}

export interface EmbeddingEventListResponse {
  events: EmbeddingEvent[];
}

export interface EmbeddingStatsResponse {
  documents_embedded: number;
  vectors: number;
  model: string;
  dimension: number;
}
