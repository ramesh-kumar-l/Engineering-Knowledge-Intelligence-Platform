import Link from "next/link";

import { Badge } from "@/components/badge";
import { fetchGraphEntities } from "@/lib/api";
import { entityKindTone } from "@/lib/format";

export const dynamic = "force-dynamic";

export default async function TeamExplorerPage() {
  const teams = await fetchGraphEntities("team");

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <Link href="/graph" className="text-xs text-muted-foreground hover:underline">
        ← Knowledge Graph
      </Link>

      <div>
        <h2 className="text-lg font-semibold tracking-tight">Team explorer</h2>
        <p className="mt-1 text-sm text-muted-foreground">
          Teams projected from repository owners. Open a team to see the repositories it
          owns and the engineers contributing to them.
        </p>
      </div>

      <section className="rounded-lg border border-border bg-card p-5">
        {teams.length === 0 ? (
          <p className="text-sm text-muted-foreground">
            No teams yet. Build the graph to project repository owners as teams.
          </p>
        ) : (
          <ul className="divide-y divide-border">
            {teams.map((team) => (
              <li
                key={team.key}
                className="flex items-center justify-between gap-3 py-3"
              >
                <Link
                  href={`/graph/entity?key=${encodeURIComponent(team.key)}`}
                  className="min-w-0 truncate text-sm font-medium hover:underline"
                >
                  {team.name}
                </Link>
                <Badge tone={entityKindTone(team.kind)} label={team.kind} />
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}
