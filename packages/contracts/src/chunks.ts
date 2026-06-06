/** Document-processing result contracts — mirror apps/api/app/domain/chunks.py. */
import type { SourceType } from "./connectors";

export type ProcessingStatus = "pending" | "processed" | "failed";

export type DocumentCategory =
  | "bug"
  | "feature"
  | "question"
  | "incident"
  | "documentation"
  | "discussion"
  | "other";

export interface Chunk {
  id: string;
  ordinal: number;
  content: string;
  char_count: number;
  token_estimate: number;
}

export interface Enrichment {
  document_id: string;
  status: ProcessingStatus;
  category: DocumentCategory;
  summary: string;
  keywords: string[];
  language: string | null;
  word_count: number;
  char_count: number;
  chunk_count: number;
  error: string | null;
  processed_at: string | null;
}

export interface ProcessedDocument {
  document_id: string;
  title: string;
  url: string | null;
  source_type: SourceType;
  external_id: string;
  enrichment: Enrichment;
}

export interface ProcessedDocumentListResponse {
  documents: ProcessedDocument[];
}

export interface DocumentProcessingDetail {
  document_id: string;
  title: string;
  url: string | null;
  source_type: SourceType;
  external_id: string;
  enrichment: Enrichment | null;
  chunks: Chunk[];
}
