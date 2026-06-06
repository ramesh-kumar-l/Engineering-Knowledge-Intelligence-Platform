/** Mirror of apps/api `HealthResponse`. */
export interface HealthResponse {
  status: string;
  version: string;
}

/** Mirror of apps/api `DependencyStatus`. */
export interface DependencyStatus {
  name: string;
  healthy: boolean;
  detail: string | null;
}

/** Mirror of apps/api `ReadinessResponse`. */
export interface ReadinessResponse {
  status: "ready" | "degraded";
  version: string;
  dependencies: DependencyStatus[];
}
