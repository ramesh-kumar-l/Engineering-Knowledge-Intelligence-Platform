import type { ReadinessResponse } from "@ekip/contracts";

/**
 * Typed server-side client for the EKIP API. Uses the shared contract types so the
 * frontend and backend cannot silently drift (risk R2).
 */
const API_URL = process.env.EKIP_API_URL ?? "http://localhost:8000";

export interface ReadinessResult {
  reachable: boolean;
  data: ReadinessResponse | null;
}

/** Fetch backend readiness. Never throws — returns reachable=false when the API is down. */
export async function fetchReadiness(): Promise<ReadinessResult> {
  try {
    const res = await fetch(`${API_URL}/health/ready`, { cache: "no-store" });
    // 200 (ready) and 503 (degraded) both carry a valid body.
    const data = (await res.json()) as ReadinessResponse;
    return { reachable: true, data };
  } catch {
    return { reachable: false, data: null };
  }
}
