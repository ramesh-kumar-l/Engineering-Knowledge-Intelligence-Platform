import Link from "next/link";
import { notFound } from "next/navigation";

import { Badge } from "@/components/badge";
import { fetchDocumentProcessing } from "@/lib/api";
import { categoryTone, formatDate, processingStatusTone } from "@/lib/format";

export const dynamic = "force-dynamic";

export default async function ParsingExplorerDetailPage({
  params,
}: {
  params: { id: string };
}) {
  const detail = await fetchDocumentProcessing(params.id);
  if (!detail) notFound();

  const { enrichment, chunks } = detail;

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <Link
        href="/processing/explorer"
        className="text-xs text-muted-foreground hover:underline"
      >
        ← Parsing explorer
      </Link>

      <div className="flex items-center justify-between">
        <div className="min-w-0">
          <h2 className="text-lg font-semibold tracking-tight">{detail.title}</h2>
          <p className="mt-1 text-sm text-muted-foreground">
            {detail.source_type} · #{detail.external_id}
            {detail.url ? (
              <>
                {" · "}
                <a
                  href={detail.url}
                  className="text-primary hover:underline"
                  target="_blank"
                  rel="noreferrer"
                >
                  source
                </a>
              </>
            ) : null}
          </p>
        </div>
        {enrichment ? (
          <div className="flex shrink-0 items-center gap-2">
            <Badge tone={categoryTone(enrichment.category)} label={enrichment.category} />
            <Badge
              tone={processingStatusTone(enrichment.status)}
              label={enrichment.status}
            />
          </div>
        ) : null}
      </div>

      {enrichment === null ? (
        <p className="rounded-md border border-border bg-card px-3 py-2 text-sm text-muted-foreground">
          This document has not been processed yet.
        </p>
      ) : (
        <>
          <section className="rounded-lg border border-border bg-card p-5">
            <h3 className="text-sm font-semibold">Summary</h3>
            <p className="mt-2 text-sm text-muted-foreground">
              {enrichment.summary || "No summary generated."}
            </p>
            <div className="mt-4 flex flex-wrap gap-1.5">
              {enrichment.keywords.map((kw) => (
                <span
                  key={kw}
                  className="rounded-md bg-muted px-2 py-0.5 text-xs text-muted-foreground"
                >
                  {kw}
                </span>
              ))}
            </div>
            <p className="mt-4 text-xs text-muted-foreground">
              {enrichment.word_count} words · {enrichment.char_count} chars ·{" "}
              {enrichment.language ?? "unknown"} · processed{" "}
              {formatDate(enrichment.processed_at)}
            </p>
            {enrichment.error ? (
              <p className="mt-3 text-sm text-danger">{enrichment.error}</p>
            ) : null}
          </section>

          <section className="rounded-lg border border-border bg-card p-5">
            <h3 className="text-sm font-semibold">Chunks ({chunks.length})</h3>
            {chunks.length === 0 ? (
              <p className="mt-3 text-sm text-muted-foreground">No chunks.</p>
            ) : (
              <ul className="mt-4 space-y-3">
                {chunks.map((chunk) => (
                  <li
                    key={chunk.id}
                    className="rounded-md border border-border bg-background p-3"
                  >
                    <p className="mb-1 text-xs text-muted-foreground">
                      #{chunk.ordinal} · {chunk.char_count} chars · ~
                      {chunk.token_estimate} tokens
                    </p>
                    <p className="whitespace-pre-wrap text-sm">{chunk.content}</p>
                  </li>
                ))}
              </ul>
            )}
          </section>
        </>
      )}
    </div>
  );
}
