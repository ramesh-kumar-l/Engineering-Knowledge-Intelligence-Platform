import Link from "next/link";
import { notFound } from "next/navigation";

import { Badge } from "@/components/badge";
import { fetchAgentRun } from "@/lib/api";
import {
  agentTypeLabel,
  confidenceTone,
  formatAge,
  formatDate,
  freshnessTone,
  riskTone,
  stepStatusTone,
  syncTone,
} from "@/lib/format";

export const dynamic = "force-dynamic";

export default async function AgentExecutionViewerPage({
  params,
}: {
  params: { id: string };
}) {
  const detail = await fetchAgentRun(params.id);
  if (detail === null) notFound();

  const { run, result, steps } = detail;

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <div>
        <Link href="/agents" className="text-sm text-primary hover:underline">
          ← Agents
        </Link>
        <div className="mt-2 flex flex-wrap items-center gap-2">
          <h2 className="text-lg font-semibold tracking-tight">{run.title}</h2>
          <Badge tone={syncTone(run.status)} label={run.status} />
          {run.confidence !== null ? (
            <Badge
              tone={confidenceTone(
                result?.confidence_band ?? "low",
              )}
              label={`confidence ${run.confidence.toFixed(2)}`}
            />
          ) : null}
        </div>
        <p className="mt-1 text-xs text-muted-foreground">
          {agentTypeLabel(run.agent_type)} · run by {run.created_by} ·{" "}
          {formatDate(run.created_at)}
        </p>
      </div>

      {result ? (
        <p className="rounded-lg border border-border bg-card p-4 text-sm">
          {result.headline}
        </p>
      ) : (
        <p className="rounded-md border border-danger/30 bg-danger/10 px-3 py-2 text-sm text-danger">
          This run did not produce a result. See the trace below.
        </p>
      )}

      {result && result.findings.length > 0 ? (
        <section className="rounded-lg border border-border bg-card p-5">
          <h3 className="text-sm font-semibold">Findings</h3>
          <ul className="mt-3 space-y-3">
            {result.findings.map((f, i) => (
              <li key={i} className="border-l-2 border-border pl-3">
                <div className="flex items-center gap-2">
                  {f.severity ? (
                    <Badge tone={riskTone(f.severity)} label={f.severity} />
                  ) : null}
                  <span className="text-sm font-medium">{f.label}</span>
                </div>
                <p className="mt-1 text-sm text-muted-foreground">{f.detail}</p>
              </li>
            ))}
          </ul>
        </section>
      ) : null}

      {result && result.actions.length > 0 ? (
        <section className="rounded-lg border border-border bg-card p-5">
          <h3 className="text-sm font-semibold">Recommended actions</h3>
          <ul className="mt-3 space-y-3">
            {result.actions.map((a, i) => (
              <li key={i} className="flex gap-3">
                <Badge tone={riskTone(a.priority)} label={a.priority} />
                <div>
                  <p className="text-sm font-medium">{a.action}</p>
                  <p className="text-xs text-muted-foreground">{a.rationale}</p>
                </div>
              </li>
            ))}
          </ul>
        </section>
      ) : null}

      {result && result.evidence.length > 0 ? (
        <section className="rounded-lg border border-border bg-card p-5">
          <h3 className="text-sm font-semibold">Evidence</h3>
          <ul className="mt-3 space-y-3">
            {result.evidence.map((e) => (
              <li key={e.document_id} className="border-l-2 border-border pl-3">
                <div className="flex flex-wrap items-center gap-2">
                  <Link
                    href={`/trust/documents/${e.document_id}`}
                    className="text-sm font-medium text-primary hover:underline"
                  >
                    {e.title}
                  </Link>
                  <Badge
                    tone={confidenceTone(e.confidence_band)}
                    label={`trust ${e.confidence_band}`}
                  />
                  <Badge tone={freshnessTone(e.freshness_band)} label={e.freshness_band} />
                  <span className="text-xs text-muted-foreground">
                    {formatAge(e.age_days)}
                  </span>
                </div>
                <p className="mt-1 text-sm text-muted-foreground">{e.snippet}</p>
                {e.owners.length > 0 ? (
                  <p className="mt-1 text-xs text-muted-foreground">
                    Owners: {e.owners.join(", ")}
                  </p>
                ) : null}
              </li>
            ))}
          </ul>
        </section>
      ) : null}

      <section className="rounded-lg border border-border bg-card p-5">
        <h3 className="text-sm font-semibold">Execution trace</h3>
        <ol className="mt-3 space-y-3">
          {steps.map((s) => (
            <li key={s.ordinal} className="flex gap-3">
              <span className="mt-0.5 text-xs text-muted-foreground">{s.ordinal + 1}.</span>
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium">{s.name}</span>
                  <Badge tone={stepStatusTone(s.status)} label={s.status} />
                </div>
                <p className="mt-1 text-sm text-muted-foreground">{s.summary}</p>
              </div>
            </li>
          ))}
        </ol>
      </section>
    </div>
  );
}
