import Link from "next/link";

import { Badge } from "@/components/badge";
import { fetchSyncRuns } from "@/lib/api";
import { formatDate, syncTone } from "@/lib/format";

export const dynamic = "force-dynamic";

export default async function SyncDashboardPage() {
  const runs = await fetchSyncRuns();

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <div>
        <h2 className="text-lg font-semibold tracking-tight">Sync dashboard</h2>
        <p className="mt-1 text-sm text-muted-foreground">
          Recent ingestion runs across all connectors.
        </p>
      </div>

      <section className="rounded-lg border border-border bg-card p-5">
        {runs.length === 0 ? (
          <p className="text-sm text-muted-foreground">
            No sync runs yet. Trigger one from a connector.
          </p>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-xs text-muted-foreground">
                <th className="pb-2 font-medium">Started</th>
                <th className="pb-2 font-medium">Documents</th>
                <th className="pb-2 font-medium">Changes</th>
                <th className="pb-2 text-right font-medium">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {runs.map((run) => (
                <tr key={run.id}>
                  <td className="py-3">
                    <Link href={`/sync/${run.id}`} className="hover:underline">
                      {formatDate(run.started_at)}
                    </Link>
                  </td>
                  <td className="py-3 text-muted-foreground">{run.documents_seen}</td>
                  <td className="py-3 text-muted-foreground">
                    +{run.created_count} ~{run.updated_count} −{run.deleted_count}
                  </td>
                  <td className="py-3 text-right">
                    <Badge tone={syncTone(run.status)} label={run.status} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>
    </div>
  );
}
