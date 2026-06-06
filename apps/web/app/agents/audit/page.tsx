import Link from "next/link";

import { Badge } from "@/components/badge";
import { fetchAgentRuns } from "@/lib/api";
import { agentTypeLabel, formatDate, syncTone } from "@/lib/format";

export const dynamic = "force-dynamic";

export default async function AgentAuditTrailPage() {
  const runs = await fetchAgentRuns();

  return (
    <div className="mx-auto max-w-5xl space-y-6">
      <div>
        <Link href="/agents" className="text-sm text-primary hover:underline">
          ← Agents
        </Link>
        <h2 className="mt-2 text-lg font-semibold tracking-tight">Agent Audit Trail</h2>
        <p className="mt-1 text-sm text-muted-foreground">
          Every agent run is recorded — who ran which agent, against what, when, and with
          what outcome. Each run links to its full execution trace. (Phase 8)
        </p>
      </div>

      {runs.length === 0 ? (
        <p className="rounded-lg border border-border bg-card p-5 text-sm text-muted-foreground">
          No agent runs recorded yet.
        </p>
      ) : (
        <div className="overflow-x-auto rounded-lg border border-border bg-card">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-xs text-muted-foreground">
                <th className="px-4 py-3 font-medium">Agent</th>
                <th className="px-4 py-3 font-medium">Target</th>
                <th className="px-4 py-3 font-medium">Status</th>
                <th className="px-4 py-3 font-medium">Run by</th>
                <th className="px-4 py-3 font-medium">When</th>
                <th className="px-4 py-3 text-right font-medium">Steps</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {runs.map((run) => (
                <tr key={run.id} className="hover:bg-muted">
                  <td className="px-4 py-3">
                    <Link
                      href={`/agents/${run.id}`}
                      className="font-medium text-primary hover:underline"
                    >
                      {agentTypeLabel(run.agent_type)}
                    </Link>
                  </td>
                  <td className="px-4 py-3 text-muted-foreground">{run.target ?? "—"}</td>
                  <td className="px-4 py-3">
                    <Badge tone={syncTone(run.status)} label={run.status} />
                  </td>
                  <td className="px-4 py-3 text-muted-foreground">{run.created_by}</td>
                  <td className="px-4 py-3 text-muted-foreground">
                    {formatDate(run.created_at)}
                  </td>
                  <td className="px-4 py-3 text-right text-muted-foreground">
                    {run.step_count}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
