import Link from "next/link";

import { buildGraphAction } from "@/app/graph/actions";
import { Badge } from "@/components/badge";
import { fetchGraphEntities, fetchGraphRuns, fetchGraphStats } from "@/lib/api";
import { entityKindTone, formatDate, syncTone } from "@/lib/format";

export const dynamic = "force-dynamic";

export default async function KnowledgeExplorerPage({
  searchParams,
}: {
  searchParams: { error?: string; kind?: string; q?: string };
}) {
  const [stats, entities, runs] = await Promise.all([
    fetchGraphStats(),
    fetchGraphEntities(searchParams.kind, searchParams.q),
    fetchGraphRuns(),
  ]);

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <h2 className="text-lg font-semibold tracking-tight">Knowledge Graph</h2>
          <p className="mt-1 text-sm text-muted-foreground">
            Entities and relationships projected from ingested data, plus curated
            architecture. (Phase 3)
          </p>
        </div>
        <form action={buildGraphAction}>
          <button
            type="submit"
            className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-white hover:opacity-90"
          >
            Build graph
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
        <Stat label="Entities" value={stats?.total_entities ?? 0} />
        <Stat label="Relationships" value={stats?.total_relationships ?? 0} />
        <Stat label="Kinds" value={Object.keys(stats?.entities_by_kind ?? {}).length} />
        <Stat
          label="Rel. types"
          value={Object.keys(stats?.relationships_by_type ?? {}).length}
        />
      </section>

      <nav className="flex flex-wrap gap-4 text-sm">
        <Link href="/graph/services" className="text-primary hover:underline">
          Service explorer →
        </Link>
        <Link href="/graph/teams" className="text-primary hover:underline">
          Team explorer →
        </Link>
        <Link href="/graph/dependencies" className="text-primary hover:underline">
          Dependency graph →
        </Link>
      </nav>

      <section className="rounded-lg border border-border bg-card p-5">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-semibold">Entities</h3>
          <form className="flex gap-2" action="/graph">
            <input
              name="q"
              defaultValue={searchParams.q ?? ""}
              placeholder="Search…"
              className="rounded-md border border-border bg-background px-2 py-1 text-xs"
            />
            <button className="text-xs text-primary hover:underline" type="submit">
              Search
            </button>
          </form>
        </div>
        {entities.length === 0 ? (
          <p className="mt-3 text-sm text-muted-foreground">
            No entities yet. Build the graph to project ingested data.
          </p>
        ) : (
          <ul className="mt-4 divide-y divide-border">
            {entities.map((entity) => (
              <li
                key={entity.key}
                className="flex items-center justify-between gap-3 py-2.5"
              >
                <Link
                  href={`/graph/entity?key=${encodeURIComponent(entity.key)}`}
                  className="min-w-0 truncate text-sm font-medium hover:underline"
                >
                  {entity.name}
                </Link>
                <div className="flex shrink-0 items-center gap-2">
                  {entity.source === "manual" ? (
                    <span className="text-xs text-muted-foreground">curated</span>
                  ) : null}
                  <Badge tone={entityKindTone(entity.kind)} label={entity.kind} />
                </div>
              </li>
            ))}
          </ul>
        )}
      </section>

      <section className="rounded-lg border border-border bg-card p-5">
        <h3 className="text-sm font-semibold">Recent build jobs</h3>
        {runs.length === 0 ? (
          <p className="mt-3 text-sm text-muted-foreground">No builds yet.</p>
        ) : (
          <table className="mt-4 w-full text-sm">
            <thead>
              <tr className="text-left text-xs text-muted-foreground">
                <th className="pb-2 font-medium">Started</th>
                <th className="pb-2 font-medium">Entities</th>
                <th className="pb-2 font-medium">Relationships</th>
                <th className="pb-2 text-right font-medium">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {runs.map((run) => (
                <tr key={run.id}>
                  <td className="py-3">
                    <Link href={`/graph/jobs/${run.id}`} className="hover:underline">
                      {formatDate(run.started_at)}
                    </Link>
                  </td>
                  <td className="py-3 text-muted-foreground">{run.entity_count}</td>
                  <td className="py-3 text-muted-foreground">
                    {run.relationship_count}
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

function Stat({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-lg border border-border bg-card p-3 text-center">
      <p className="text-lg font-semibold">{value}</p>
      <p className="text-xs text-muted-foreground">{label}</p>
    </div>
  );
}
