import Link from "next/link";

import { Badge } from "@/components/badge";
import { fetchDependencyIntel } from "@/lib/api";
import { entityKindTone, riskTone } from "@/lib/format";

export const dynamic = "force-dynamic";

export default async function DependencyRiskPage() {
  const report = await fetchDependencyIntel();

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <h2 className="text-lg font-semibold tracking-tight">Dependency Risk</h2>
          <p className="mt-1 text-sm text-muted-foreground">
            Components ranked by blast radius — how many others depend on them — plus any
            circular dependencies. Curate <code>depends_on</code> edges in the Knowledge
            Graph to populate this. (Phase 7)
          </p>
        </div>
        <Link href="/intelligence" className="text-sm text-primary hover:underline">
          ← Intelligence
        </Link>
      </div>

      {report && report.cycle_count > 0 ? (
        <section className="rounded-lg border border-danger/40 bg-danger/5 p-5">
          <h3 className="text-sm font-semibold text-danger">
            Circular dependencies ({report.cycle_count})
          </h3>
          <ul className="mt-3 space-y-2">
            {report.cycles.map((c, idx) => (
              <li key={idx} className="text-sm text-muted-foreground">
                {c.members.map((m) => m.name).join(" → ")} →{" "}
                {c.members[0]?.name}
              </li>
            ))}
          </ul>
        </section>
      ) : null}

      <section className="rounded-lg border border-border bg-card p-5">
        <h3 className="text-sm font-semibold">
          Components{" "}
          <span className="text-muted-foreground">({report?.total_nodes ?? 0})</span>
        </h3>
        {!report || report.nodes.length === 0 ? (
          <p className="mt-3 text-sm text-muted-foreground">
            No dependencies yet. Declare services and <code>depends_on</code>{" "}
            relationships in the Knowledge Graph.
          </p>
        ) : (
          <table className="mt-4 w-full text-sm">
            <thead>
              <tr className="text-left text-xs text-muted-foreground">
                <th className="pb-2 font-medium">Component</th>
                <th className="pb-2 font-medium">Kind</th>
                <th className="pb-2 text-right font-medium">Depended on by</th>
                <th className="pb-2 text-right font-medium">Depends on</th>
                <th className="pb-2 font-medium">Risk</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {report.nodes.map((n) => (
                <tr key={n.key}>
                  <td className="py-3 font-medium">
                    {n.name}
                    {n.in_cycle ? (
                      <span className="ml-2 text-xs text-danger">in cycle</span>
                    ) : null}
                  </td>
                  <td className="py-3">
                    <Badge tone={entityKindTone(n.kind)} label={n.kind} />
                  </td>
                  <td className="py-3 text-right text-muted-foreground">{n.fan_in}</td>
                  <td className="py-3 text-right text-muted-foreground">{n.fan_out}</td>
                  <td className="py-3">
                    <Badge
                      tone={riskTone(n.risk_band)}
                      label={`${n.risk_band} ${n.risk_score.toFixed(2)}`}
                    />
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
