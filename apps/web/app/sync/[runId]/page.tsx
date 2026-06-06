import Link from "next/link";
import { notFound } from "next/navigation";

import type { SyncEventLevel } from "@ekip/contracts";

import { Badge, type Tone } from "@/components/badge";
import { fetchSyncEvents, fetchSyncRun } from "@/lib/api";
import { formatDate, syncTone } from "@/lib/format";

export const dynamic = "force-dynamic";

const LEVEL_TONE: Record<SyncEventLevel, Tone> = {
  info: "muted",
  warning: "warning",
  error: "danger",
};

export default async function SyncLogsPage({ params }: { params: { runId: string } }) {
  const run = await fetchSyncRun(params.runId);
  if (!run) notFound();

  const events = await fetchSyncEvents(run.id);

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <Link
        href={`/connectors/${run.connector_id}`}
        className="text-xs text-muted-foreground hover:underline"
      >
        ← Connector
      </Link>

      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold tracking-tight">Sync run</h2>
          <p className="mt-1 text-sm text-muted-foreground">
            Started {formatDate(run.started_at)} · finished {formatDate(run.finished_at)}
          </p>
        </div>
        <Badge tone={syncTone(run.status)} label={run.status} />
      </div>

      <section className="grid grid-cols-2 gap-3 sm:grid-cols-5">
        <Stat label="Seen" value={run.documents_seen} />
        <Stat label="Created" value={run.created_count} />
        <Stat label="Updated" value={run.updated_count} />
        <Stat label="Deleted" value={run.deleted_count} />
        <Stat label="Unchanged" value={run.unchanged_count} />
      </section>

      {run.error ? (
        <p className="rounded-md border border-danger/30 bg-danger/10 px-3 py-2 text-sm text-danger">
          {run.error}
        </p>
      ) : null}

      <section className="rounded-lg border border-border bg-card p-5">
        <h3 className="text-sm font-semibold">Logs</h3>
        {events.length === 0 ? (
          <p className="mt-3 text-sm text-muted-foreground">No log events.</p>
        ) : (
          <ul className="mt-4 space-y-2">
            {events.map((event) => (
              <li key={event.id} className="flex items-start gap-3 text-sm">
                <Badge tone={LEVEL_TONE[event.level]} label={event.level} />
                <div className="min-w-0">
                  <p>{event.message}</p>
                  <p className="text-xs text-muted-foreground">
                    {formatDate(event.created_at)}
                  </p>
                </div>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-lg border border-border bg-card p-3 text-center">
      <p className="text-lg font-semibold">{value}</p>
      <p className="text-xs text-muted-foreground">{label}</p>
    </div>
  );
}
