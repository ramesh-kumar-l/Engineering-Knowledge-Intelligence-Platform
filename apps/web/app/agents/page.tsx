import Link from "next/link";

import { Badge } from "@/components/badge";
import { fetchAgentCatalog, fetchAgentRuns } from "@/lib/api";
import { agentTypeLabel, formatDate, syncTone } from "@/lib/format";

import { runAgentAction } from "./actions";

export const dynamic = "force-dynamic";

export default async function AgentWorkspacePage({
  searchParams,
}: {
  searchParams: { error?: string };
}) {
  const [agents, runs] = await Promise.all([fetchAgentCatalog(), fetchAgentRuns()]);

  return (
    <div className="mx-auto max-w-5xl space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <h2 className="text-lg font-semibold tracking-tight">Agents</h2>
          <p className="mt-1 text-sm text-muted-foreground">
            Run a deterministic agent over your knowledge — it composes retrieval, the
            graph, trust and intelligence into an auditable, evidence-backed result.
            (Phase 8)
          </p>
        </div>
        <Link href="/agents/audit" className="text-sm text-primary hover:underline">
          Audit trail →
        </Link>
      </div>

      {searchParams.error ? (
        <p className="rounded-md border border-danger/30 bg-danger/10 px-3 py-2 text-sm text-danger">
          {searchParams.error}
        </p>
      ) : null}

      {agents.length === 0 ? (
        <p className="rounded-lg border border-border bg-card p-5 text-sm text-muted-foreground">
          The agent catalog is unavailable — the API may be unreachable.
        </p>
      ) : (
        <section className="grid gap-4 md:grid-cols-2">
          {agents.map((agent) => (
            <form
              key={agent.type}
              action={runAgentAction}
              className="flex flex-col gap-3 rounded-lg border border-border bg-card p-5"
            >
              <input type="hidden" name="agent_type" value={agent.type} />
              <h3 className="text-sm font-semibold">{agent.label}</h3>
              <p className="text-xs text-muted-foreground">{agent.description}</p>
              {agent.needs_target ? (
                <input
                  type="text"
                  name="target"
                  placeholder={agent.target_hint}
                  className="rounded-md border border-border bg-background px-3 py-2 text-sm"
                />
              ) : (
                <p className="text-xs text-muted-foreground italic">
                  Scans the whole corpus — no target needed.
                </p>
              )}
              <button
                type="submit"
                className="self-start rounded-md bg-primary px-4 py-2 text-sm font-medium text-white hover:opacity-90"
              >
                Run agent
              </button>
            </form>
          ))}
        </section>
      )}

      <section>
        <h3 className="text-sm font-semibold">Recent runs</h3>
        {runs.length === 0 ? (
          <p className="mt-2 text-sm text-muted-foreground">
            No agent runs yet. Launch one above to get started.
          </p>
        ) : (
          <ul className="mt-3 divide-y divide-border rounded-lg border border-border bg-card">
            {runs.slice(0, 8).map((run) => (
              <li key={run.id}>
                <Link
                  href={`/agents/${run.id}`}
                  className="flex items-center justify-between gap-3 px-4 py-3 hover:bg-muted"
                >
                  <span className="flex min-w-0 items-center gap-2">
                    <Badge tone={syncTone(run.status)} label={run.status} />
                    <span className="truncate text-sm font-medium">{run.title}</span>
                  </span>
                  <span className="shrink-0 text-xs text-muted-foreground">
                    {agentTypeLabel(run.agent_type)} · {formatDate(run.created_at)}
                  </span>
                </Link>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}
