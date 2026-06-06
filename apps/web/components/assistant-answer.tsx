import Link from "next/link";

import type { AnswerBody } from "@ekip/contracts";

import { Badge } from "@/components/badge";
import {
  confidenceTone,
  entityKindTone,
  formatAge,
  freshnessTone,
  intentLabel,
  relationshipLabel,
} from "@/lib/format";

/**
 * Presentational assistant answer: the summary with its overall trust, the key
 * points, every citation with Phase-5 trust (linking to the Trust Inspector), and
 * the related graph facts / entities that informed it. Used in the conversation
 * thread; the Evidence Viewer reuses the citation rendering at corpus scale.
 */
export function AssistantAnswer({ answer }: { answer: AnswerBody }) {
  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-2">
        <Badge tone="info" label={intentLabel(answer.intent)} />
        <Badge
          tone={confidenceTone(answer.confidence_band)}
          label={`confidence ${answer.confidence_band} ${answer.confidence.toFixed(2)}`}
        />
      </div>

      <p className="text-sm leading-relaxed">{answer.summary}</p>

      {answer.key_points.length > 0 ? (
        <ul className="list-disc space-y-1 pl-5 text-sm text-muted-foreground">
          {answer.key_points.map((point, i) => (
            <li key={i}>{point}</li>
          ))}
        </ul>
      ) : null}

      {answer.citations.length > 0 ? (
        <section>
          <h4 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
            Evidence ({answer.citations.length})
          </h4>
          <ul className="mt-2 space-y-2">
            {answer.citations.map((c, i) => (
              <li
                key={`${c.chunk_id ?? c.document_id}-${i}`}
                className="rounded-md border border-border bg-background p-3"
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
                <p className="mt-1.5 text-sm text-muted-foreground">{c.snippet}</p>
                <div className="mt-1.5 flex flex-wrap gap-x-3 text-xs text-muted-foreground">
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
                </div>
              </li>
            ))}
          </ul>
        </section>
      ) : null}

      {answer.relations.length > 0 ? (
        <section>
          <h4 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
            Related facts
          </h4>
          <ul className="mt-2 space-y-1 text-sm text-muted-foreground">
            {answer.relations.map((r) => (
              <li key={`${r.relation}-${r.key}`}>
                <span className="text-muted-foreground/70">{relationshipLabel(r.relation)}</span>{" "}
                <Link
                  href={`/graph/entity?key=${encodeURIComponent(r.key)}`}
                  className="hover:underline"
                >
                  {r.name}
                </Link>
              </li>
            ))}
          </ul>
        </section>
      ) : null}

      {answer.entities.length > 0 ? (
        <section>
          <h4 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
            Related entities
          </h4>
          <ul className="mt-2 flex flex-wrap gap-2">
            {answer.entities.map((e) => (
              <li key={e.key}>
                <Link href={`/graph/entity?key=${encodeURIComponent(e.key)}`}>
                  <Badge tone={entityKindTone(e.kind)} label={`${e.name} · ${e.kind}`} />
                </Link>
              </li>
            ))}
          </ul>
        </section>
      ) : null}
    </div>
  );
}
