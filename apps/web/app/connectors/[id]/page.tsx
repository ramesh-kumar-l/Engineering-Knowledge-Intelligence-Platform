import Link from "next/link";
import { notFound } from "next/navigation";

import { triggerSyncAction } from "@/app/connectors/actions";
import { Badge } from "@/components/badge";
import { fetchConnector, fetchSyncRuns } from "@/lib/api";
import { connectorTone, formatDate, syncTone } from "@/lib/format";

export const dynamic = "force-dynamic";

export default async function ConnectorDetailPage({
  params,
  searchParams,
}: {
  params: { id: string };
  searchParams: { error?: string };
}) {
  const connector = await fetchConnector(params.id);
  if (!connector) notFound();

  const runs = await fetchSyncRuns(connector.id);

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <Link href="/connectors" className="text-xs text-muted-foreground hover:underline">
        ← Connectors
      </Link>

      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold tracking-tight">{connector.name}</h2>
          <p className="mt-1 text-sm text-muted-foreground">
            {connector.source_type} · last synced {formatDate(connector.last_synced_at)}
          </p>
        </div>
        <Badge tone={connectorTone(connector.status)} label={connector.status} />
      </div>

      {searchParams.error ? (
        <p
          role="alert"
          className="rounded-md border border-danger/30 bg-danger/10 px-3 py-2 text-sm text-danger"
        >
          {searchParams.error}
        </p>
      ) : null}

      <section className="flex items-center justify-between rounded-lg border border-border bg-card p-5">
        <p className="text-sm text-muted-foreground">
          Run an incremental sync to ingest new and changed documents.
        </p>
        <form action={triggerSyncAction}>
          <input type="hidden" name="connector_id" value={connector.id} />
          <button
            type="submit"
            className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-white hover:opacity-90"
          >
            Run sync
          </button>
        </form>
      </section>

      <section className="rounded-lg border border-border bg-card p-5">
        <h3 className="text-sm font-semibold">Sync runs</h3>
        {runs.length === 0 ? (
          <p className="mt-3 text-sm text-muted-foreground">No sync runs yet.</p>
        ) : (
          <ul className="mt-4 divide-y divide-border">
            {runs.map((run) => (
              <li key={run.id} className="flex items-center justify-between py-3">
                <div>
                  <Link
                    href={`/sync/${run.id}`}
                    className="text-sm font-medium hover:underline"
                  >
                    {formatDate(run.started_at)}
                  </Link>
                  <p className="text-xs text-muted-foreground">
                    +{run.created_count} ~{run.updated_count} −{run.deleted_count} ={" "}
                    {run.unchanged_count} unchanged
                  </p>
                </div>
                <Badge tone={syncTone(run.status)} label={run.status} />
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}
