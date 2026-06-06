import Link from "next/link";
import { notFound } from "next/navigation";

import type { Citation } from "@ekip/contracts";

import { Badge } from "@/components/badge";
import { fetchConversation } from "@/lib/api";
import { confidenceTone, formatAge, freshnessTone } from "@/lib/format";

export const dynamic = "force-dynamic";

/** Collapse every cited document across the thread, keeping its highest-trust hit. */
function collectEvidence(
  messages: { answer: { citations: Citation[] } | null }[],
): Citation[] {
  const best = new Map<string, Citation>();
  for (const message of messages) {
    for (const citation of message.answer?.citations ?? []) {
      const existing = best.get(citation.document_id);
      if (!existing || citation.confidence > existing.confidence) {
        best.set(citation.document_id, citation);
      }
    }
  }
  return [...best.values()].sort((a, b) => b.confidence - a.confidence);
}

export default async function EvidenceViewerPage({
  params,
}: {
  params: { id: string };
}) {
  const detail = await fetchConversation(params.id);
  if (detail === null) notFound();
  const evidence = collectEvidence(detail.messages);

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <h2 className="text-lg font-semibold tracking-tight">Evidence Viewer</h2>
          <p className="mt-1 text-sm text-muted-foreground">
            Every source cited in “{detail.conversation.title}”, ranked by confidence.
            (Phase 6)
          </p>
        </div>
        <Link
          href={`/assistant/${detail.conversation.id}`}
          className="shrink-0 text-sm text-primary hover:underline"
        >
          ← Conversation
        </Link>
      </div>

      <section className="rounded-lg border border-border bg-card p-5">
        <h3 className="text-sm font-semibold">
          Cited sources <span className="text-muted-foreground">({evidence.length})</span>
        </h3>
        {evidence.length === 0 ? (
          <p className="mt-3 text-sm text-muted-foreground">
            No evidence was cited in this conversation yet.
          </p>
        ) : (
          <ul className="mt-4 space-y-3">
            {evidence.map((c) => (
              <li
                key={c.document_id}
                className="rounded-md border border-border bg-background p-4"
              >
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <Link
                    href={`/trust/documents/${c.document_id}`}
                    className="text-sm font-medium hover:underline"
                  >
                    {c.title}
                  </Link>
                  <div className="flex items-center gap-1.5">
                    <Badge
                      tone={confidenceTone(c.confidence_band)}
                      label={`${c.confidence_band} ${c.confidence.toFixed(2)}`}
                    />
                    <Badge tone={freshnessTone(c.freshness_band)} label={c.freshness_band} />
                  </div>
                </div>
                <p className="mt-2 text-sm text-muted-foreground">{c.snippet}</p>
                <div className="mt-2 flex flex-wrap gap-x-3 text-xs text-muted-foreground">
                  <span>{c.source_type}</span>
                  <span>{formatAge(c.age_days)}</span>
                  <span>
                    {c.ownership_known
                      ? `owner: ${c.owners.map((o) => o.name).join(", ")}`
                      : "owner: unknown"}
                  </span>
                  {c.url ? (
                    <a
                      href={c.url}
                      target="_blank"
                      rel="noreferrer"
                      className="text-primary hover:underline"
                    >
                      source ↗
                    </a>
                  ) : null}
                  <Link
                    href={`/trust/documents/${c.document_id}`}
                    className="text-primary hover:underline"
                  >
                    trust inspector →
                  </Link>
                </div>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}
