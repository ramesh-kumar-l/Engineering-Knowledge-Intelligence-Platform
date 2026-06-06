/** Trust contracts — mirror apps/api/app/domain/trust.py. */
import type { SourceType } from "./connectors";

export type ConfidenceBand = "high" | "medium" | "low";
export type FreshnessBand = "fresh" | "recent" | "aging" | "stale";

export interface OwnerRef {
  key: string;
  name: string;
}

export interface SourceInfo {
  source_type: SourceType;
  connector_id: string;
  external_id: string;
  title: string;
  url: string | null;
  source_updated_at: string | null;
  ingested_at: string;
}

export interface EvidenceItem {
  chunk_id: string;
  ordinal: number;
  snippet: string;
}

export interface TrustProfileResponse {
  document_id: string;
  title: string;
  confidence: number;
  confidence_band: ConfidenceBand;
  freshness: number;
  freshness_band: FreshnessBand;
  age_days: number | null;
  signals: Record<string, number>;
  source: SourceInfo;
  owners: OwnerRef[];
  ownership_known: boolean;
  evidence: EvidenceItem[];
}

export interface SourceTrustItem {
  document_id: string;
  title: string;
  source_type: SourceType;
  url: string | null;
  confidence: number;
  confidence_band: ConfidenceBand;
  freshness_band: FreshnessBand;
  age_days: number | null;
  has_owner: boolean;
}

export interface SourceListResponse {
  sources: SourceTrustItem[];
}

export interface FreshnessBucket {
  band: FreshnessBand;
  count: number;
}

export interface FreshnessResponse {
  total: number;
  buckets: FreshnessBucket[];
  stale: SourceTrustItem[];
}
