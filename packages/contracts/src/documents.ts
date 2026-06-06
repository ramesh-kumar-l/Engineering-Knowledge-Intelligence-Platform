/** Document contracts — mirror apps/api/app/domain/documents.py. */
import type { SourceType } from "./connectors";

export interface Document {
  id: string;
  connector_id: string;
  source_type: SourceType;
  external_id: string;
  title: string;
  url: string | null;
  content_hash: string;
  metadata: Record<string, unknown>;
  source_updated_at: string | null;
  is_deleted: boolean;
  created_at: string;
  updated_at: string;
}

export interface DocumentListResponse {
  documents: Document[];
}
