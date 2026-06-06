/** Search contracts — mirror apps/api/app/domain/search.py. */
import type { EntityKind } from "./graph";

export type SearchMode = "keyword" | "vector" | "hybrid";

export interface SearchChunkHit {
  chunk_id: string;
  document_id: string;
  ordinal: number;
  title: string;
  url: string | null;
  snippet: string;
  score: number;
  keyword_rank: number | null;
  vector_rank: number | null;
}

export interface SearchEntityHit {
  key: string;
  kind: EntityKind;
  name: string;
  summary: string | null;
  score: number;
}

export interface SearchResponse {
  query: string;
  mode: SearchMode;
  chunks: SearchChunkHit[];
  entities: SearchEntityHit[];
}
