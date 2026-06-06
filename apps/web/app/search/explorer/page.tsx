import Link from "next/link";

import { embedAction } from "@/app/search/actions";
import { Badge } from "@/components/badge";
import { fetchEmbeddingRuns, fetchEmbeddingStats } from "@/lib/api";
import { formatDate, syncTone } from "@/lib/format";

export const dynamic = "force-dynamic";

export default async function SearchExplorerPage({
  searchParams,
}: {
  searchParams: { error?: string };
}) {
  const [stats, runs] = await Promise.all([
    fetchEmbeddingStats(),
    fetchEmbeddingRuns(),
  ]);

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <h2 className="text-lg font-semibold tracking-tight">Search Explorer</h2>
          <p className="mt-1 text-sm text-muted-foreground">
            The vector index that powers search. Embed processed chunks to make them
            retrievable. (Phase 4)
          </p>
        </div>
        <form action={embedAction}>
          <button
            type="submit"
            className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-white hover:opacity-90"
          >
            Embed corpus
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
        <Stat label="Documents embedded" value={String(stats?.documents_embedded ?? 0)} />
        <Stat label="Vectors" value={String(stats?.vectors ?? 0)} />
        <Stat label="Model" value={stats?.model ?? "—"} />
        <Stat label="Dimensions" value={String(stats?.dimension ?? 0)} />
      </section>

      <nav className="flex flex-wrap gap-4 text-sm">
        <Link href="/search" className="text-primary hover:underline">
          Search →
        </Link>
        <Link href="/search/advanced" className="text-primary hover:underline">
          Advanced search →
        </Link>
      </nav>

      <section className="rounded-lg border border-border bg-card p-5">
        <h3 className="text-sm font-semibold">Recent embedding jobs</h3>
        {runs.length === 0 ? (
          <p className="mt-3 text-sm text-muted-foreground">
            No embedding runs yet. Embed the corpus to build the index.
          </p>
        ) : (
          <table className="mt-4 w-full text-sm">
            <thead>
              <tr className="text-left text-xs text-muted-foreground">
                <th className="pb-2 font-medium">Started</th>
                <th className="pb-2 font-medium">Embedded</th>
                <th className="pb-2 font-medium">Chunks</th>
                <th className="pb-2 text-right font-medium">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {runs.map((run) => (
                <tr key={run.id}>
                  <td className="py-3">
                    <Link
                      href={`/search/jobs/${run.id}`}
                      className="hover:underline"
                    >
                      {formatDate(run.started_at)}
                    </Link>
                  </td>
                  <td className="py-3 text-muted-foreground">
                    {run.documents_embedded} / {run.documents_seen}
                  </td>
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

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-border bg-card p-3 text-center">
      <p className="truncate text-lg font-semibold">{value}</p>
      <p className="text-xs text-muted-foreground">{label}</p>
    </div>
  );
}
