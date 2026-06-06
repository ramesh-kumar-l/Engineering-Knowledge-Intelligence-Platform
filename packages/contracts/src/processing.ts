/** Processing contracts — mirror apps/api/app/domain/processing.py. */
import type { SyncEventLevel, SyncStatus } from "./sync";

export interface ProcessingRun {
  id: string;
  connector_id: string | null;
  status: SyncStatus;
  documents_seen: number;
  processed_count: number;
  chunk_count: number;
  failed_count: number;
  error: string | null;
  started_at: string;
  finished_at: string | null;
}

export interface ProcessingRunListResponse {
  runs: ProcessingRun[];
}

export interface ProcessingEvent {
  id: string;
  level: SyncEventLevel;
  message: string;
  created_at: string;
}

export interface ProcessingEventListResponse {
  events: ProcessingEvent[];
}

export interface ChunkStatsResponse {
  documents_processed: number;
  total_chunks: number;
  total_chunk_chars: number;
  avg_chunks_per_document: number;
  avg_chunk_chars: number;
  category_distribution: Record<string, number>;
}

export interface ProcessingTriggerRequest {
  connector_id?: string | null;
  limit?: number;
}
