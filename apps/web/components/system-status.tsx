import { StatusBadge } from "@/components/status-badge";
import { fetchReadiness } from "@/lib/api";

/**
 * System status card — the walking-skeleton's end-to-end proof: the web app
 * (server component) calls the API readiness endpoint and renders backend +
 * datastore health (api_catalog.md GET /health/ready).
 */
export async function SystemStatus() {
  const { reachable, data } = await fetchReadiness();

  if (!reachable || !data) {
    return (
      <section className="rounded-lg border border-border bg-card p-5">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-semibold">System status</h2>
          <StatusBadge healthy={false} label="API unreachable" />
        </div>
        <p className="mt-2 text-sm text-muted-foreground">
          Could not reach the EKIP API. Start it with{" "}
          <code className="text-foreground">uvicorn app.main:app</code> and ensure{" "}
          <code className="text-foreground">EKIP_API_URL</code> is set.
        </p>
      </section>
    );
  }

  const overallHealthy = data.status === "ready";

  return (
    <section className="rounded-lg border border-border bg-card p-5">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-semibold">System status</h2>
        <StatusBadge
          healthy={overallHealthy}
          label={overallHealthy ? "Ready" : "Degraded"}
        />
      </div>
      <p className="mt-1 text-xs text-muted-foreground">API version {data.version}</p>
      <ul className="mt-4 space-y-2">
        {data.dependencies.map((dep) => (
          <li
            key={dep.name}
            className="flex items-center justify-between rounded-md bg-muted px-3 py-2"
          >
            <span className="text-sm capitalize">{dep.name}</span>
            <StatusBadge
              healthy={dep.healthy}
              label={dep.healthy ? "Healthy" : (dep.detail ?? "Unavailable")}
            />
          </li>
        ))}
      </ul>
    </section>
  );
}
