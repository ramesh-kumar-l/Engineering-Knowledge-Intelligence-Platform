import Link from "next/link";

import { runProcessingAction } from "@/app/processing/actions";
import { Badge } from "@/components/badge";
import { fetchProcessingRuns, fetchProcessingStats } from "@/lib/api";
import { formatDate, syncTone } from "@/lib/format";

export const dynamic = "force-dynamic";

export default async function ProcessingDashboardPage({
  searchParams,
}: {
  searchParams: { error?: string };
}) {
  const [stats, runs] = await Promise.all([
    fetchProcessingStats(),
    fetchProcessingRuns(),
  ]);

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <h2 className="text-lg font-semibold tracking-tight">Processing</h2>
          <p className="mt-1 text-sm text-muted-foreground">
            Parse, chunk, classify, enrich and summarize ingested documents. (Phase 2)
          </p>
        </div>
        <form action={runProcessingAction}>
          <button
            type="submit"
            className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-white hover:opacity-90"
          >
            Run processing
          </button>
        </form>
      </div>

      {searchParams.error ? (
        <p
          role="alert"
          className="rounded-md border border-danger/30 bg-danger/10 px-3 py-2 text-sm text-danger"
        >
          {searchParams.error}
        </p>
      ) : null}

      <section className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <Stat label="Documents processed" value={stats?.documents_processed ?? 0} />
        <Stat label="Total chunks" value={stats?.total_chunks ?? 0} />
        <Stat
          label="Avg chunks / doc"
          value={stats?.avg_chunks_per_document ?? 0}
        />
        <Stat label="Avg chunk chars" value={stats?.avg_chunk_chars ?? 0} />
      </section>

      <nav className="flex gap-4 text-sm">
        <Link href="/processing/chunks" className="text-primary hover:underline">
          Chunk statistics →
        </Link>
        <Link href="/processing/explorer" className="text-primary hover:underline">
          Parsing explorer →
        </Link>
      </nav>

      <section className="rounded-lg border border-border bg-card p-5">
        <h3 className="text-sm font-semibold">Recent processing jobs</h3>
        {runs.length === 0 ? (
          <p className="mt-3 text-sm text-muted-foreground">
            No processing runs yet. Run processing to populate chunks and enrichment.
          </p>
        ) : (
          <table className="mt-4 w-full text-sm">
            <thead>
              <tr className="text-left text-xs text-muted-foreground">
                <th className="pb-2 font-medium">Started</th>
                <th className="pb-2 font-medium">Seen</th>
                <th className="pb-2 font-medium">Processed</th>
                <th className="pb-2 font-medium">Chunks</th>
                <th className="pb-2 text-right font-medium">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {runs.map((run) => (
                <tr key={run.id}>
                  <td className="py-3">
                    <Link
                      href={`/processing/jobs/${run.id}`}
                      className="hover:underline"
                    >
                      {formatDate(run.started_at)}
                    </Link>
                  </td>
                  <td className="py-3 text-muted-foreground">{run.documents_seen}</td>
                  <td className="py-3 text-muted-foreground">{run.processed_count}</td>
                  <td className="py-3 text-muted-foreground">{run.chunk_count}</td>
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

function Stat({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-lg border border-border bg-card p-3 text-center">
      <p className="text-lg font-semibold">{value}</p>
      <p className="text-xs text-muted-foreground">{label}</p>
    </div>
  );
}
