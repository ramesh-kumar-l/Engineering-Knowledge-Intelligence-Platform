import Link from "next/link";

import { Badge } from "@/components/badge";
import {
  fetchIncidentIntel,
  fetchIntelligenceOverview,
  fetchOwnershipIntel,
} from "@/lib/api";
import { entityKindTone, formatPercent } from "@/lib/format";

export const dynamic = "force-dynamic";

function Stat({
  label,
  value,
  hint,
  tone,
}: {
  label: string;
  value: string | number;
  hint?: string;
  tone?: "danger" | "warning" | "default";
}) {
  const valueClass =
    tone === "danger"
      ? "text-danger"
      : tone === "warning"
        ? "text-yellow-500"
        : "text-foreground";
  return (
    <div className="rounded-lg border border-border bg-card p-4">
      <p className="text-xs text-muted-foreground">{label}</p>
      <p className={`mt-1 text-2xl font-semibold ${valueClass}`}>{value}</p>
      {hint ? <p className="mt-1 text-xs text-muted-foreground">{hint}</p> : null}
    </div>
  );
}

export default async function IntelligenceDashboardPage() {
  const [overview, incidents, ownership] = await Promise.all([
    fetchIntelligenceOverview(),
    fetchIncidentIntel(),
    fetchOwnershipIntel(),
  ]);

  return (
    <div className="mx-auto max-w-5xl space-y-6">
      <div>
        <h2 className="text-lg font-semibold tracking-tight">Intelligence Dashboard</h2>
        <p className="mt-1 text-sm text-muted-foreground">
          Engineering intelligence over the knowledge graph and trust layer — dependency
          risk, technical debt, incidents and ownership. Computed on read; every signal
          traces to evidence. (Phase 7)
        </p>
      </div>

      {overview === null ? (
        <p className="rounded-lg border border-border bg-card p-5 text-sm text-muted-foreground">
          Intelligence is unavailable — the API may be unreachable.
        </p>
      ) : (
        <section className="grid grid-cols-2 gap-4 sm:grid-cols-4">
          <Stat
            label="High-risk dependencies"
            value={overview.dependency_high_risk}
            hint={`${overview.dependency_cycles} cycle(s)`}
            tone={overview.dependency_high_risk > 0 ? "danger" : "default"}
          />
          <Stat
            label="Documents in debt"
            value={overview.debt_count}
            hint={`${overview.debt_high} high severity`}
            tone={overview.debt_high > 0 ? "danger" : "default"}
          />
          <Stat
            label="Unresolved incidents"
            value={overview.incidents_unresolved}
            hint={`${overview.incidents_total} total`}
            tone={overview.incidents_unresolved > 0 ? "warning" : "default"}
          />
          <Stat
            label="Ownership coverage"
            value={formatPercent(overview.ownership_coverage)}
            hint="repos · services · docs"
            tone={overview.ownership_coverage < 0.5 ? "warning" : "default"}
          />
        </section>
      )}

      <section className="flex gap-3">
        <Link
          href="/intelligence/dependencies"
          className="rounded-md border border-border bg-card px-4 py-2 text-sm hover:bg-muted"
        >
          Dependency Risk →
        </Link>
        <Link
          href="/intelligence/debt"
          className="rounded-md border border-border bg-card px-4 py-2 text-sm hover:bg-muted"
        >
          Technical Debt →
        </Link>
      </section>

      <section className="rounded-lg border border-border bg-card p-5">
        <h3 className="text-sm font-semibold">
          Incidents{" "}
          <span className="text-muted-foreground">
            ({incidents?.total_incidents ?? 0})
          </span>
        </h3>
        {!incidents || incidents.incidents.length === 0 ? (
          <p className="mt-3 text-sm text-muted-foreground">
            No incidents in the graph. Build the graph from incident-classified documents.
          </p>
        ) : (
          <table className="mt-4 w-full text-sm">
            <thead>
              <tr className="text-left text-xs text-muted-foreground">
                <th className="pb-2 font-medium">Incident</th>
                <th className="pb-2 font-medium">Status</th>
                <th className="pb-2 text-right font-medium">Impacted</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {incidents.incidents.slice(0, 10).map((i) => (
                <tr key={i.key}>
                  <td className="py-2">{i.name}</td>
                  <td className="py-2">
                    <Badge
                      tone={i.resolved ? "success" : "danger"}
                      label={i.resolved ? "resolved" : "open"}
                    />
                  </td>
                  <td className="py-2 text-right text-muted-foreground">
                    {i.impacted_count}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>

      <section className="grid gap-4 md:grid-cols-2">
        <div className="rounded-lg border border-border bg-card p-5">
          <h3 className="text-sm font-semibold">Ownership coverage</h3>
          <table className="mt-4 w-full text-sm">
            <tbody className="divide-y divide-border">
              {(ownership?.coverages ?? []).map((c) => (
                <tr key={c.kind}>
                  <td className="py-2 capitalize">{c.kind}</td>
                  <td className="py-2 text-right text-muted-foreground">
                    {c.owned}/{c.total} ({formatPercent(c.coverage)})
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="rounded-lg border border-border bg-card p-5">
          <h3 className="text-sm font-semibold">
            Orphaned components{" "}
            <span className="text-muted-foreground">
              ({ownership?.orphans.length ?? 0})
            </span>
          </h3>
          {!ownership || ownership.orphans.length === 0 ? (
            <p className="mt-3 text-sm text-muted-foreground">
              No orphaned components — everything tracked has an owner.
            </p>
          ) : (
            <ul className="mt-3 space-y-2">
              {ownership.orphans.slice(0, 8).map((o) => (
                <li key={o.key} className="flex items-center gap-2 text-sm">
                  <Badge tone={entityKindTone(o.kind)} label={o.kind} />
                  <span className="text-muted-foreground">{o.name}</span>
                </li>
              ))}
            </ul>
          )}
        </div>
      </section>
    </div>
  );
}
