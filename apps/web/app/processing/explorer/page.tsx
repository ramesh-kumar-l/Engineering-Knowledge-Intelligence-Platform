import Link from "next/link";

import { Badge } from "@/components/badge";
import { fetchProcessedDocuments } from "@/lib/api";
import { categoryTone, processingStatusTone } from "@/lib/format";

export const dynamic = "force-dynamic";

export default async function ParsingExplorerPage() {
  const documents = await fetchProcessedDocuments();

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <Link href="/processing" className="text-xs text-muted-foreground hover:underline">
        ← Processing
      </Link>

      <div>
        <h2 className="text-lg font-semibold tracking-tight">Parsing explorer</h2>
        <p className="mt-1 text-sm text-muted-foreground">
          Inspect how each document was parsed, classified and chunked.
        </p>
      </div>

      <section className="rounded-lg border border-border bg-card p-5">
        {documents.length === 0 ? (
          <p className="text-sm text-muted-foreground">
            No processed documents yet. Run processing first.
          </p>
        ) : (
          <ul className="divide-y divide-border">
            {documents.map((doc) => (
              <li
                key={doc.document_id}
                className="flex items-center justify-between gap-3 py-3"
              >
                <div className="min-w-0">
                  <Link
                    href={`/processing/explorer/${doc.document_id}`}
                    className="text-sm font-medium hover:underline"
                  >
                    {doc.title}
                  </Link>
                  <p className="truncate text-xs text-muted-foreground">
                    {doc.enrichment.summary || "No summary"}
                  </p>
                </div>
                <div className="flex shrink-0 items-center gap-2">
                  <span className="text-xs text-muted-foreground">
                    {doc.enrichment.chunk_count} chunks
                  </span>
                  <Badge
                    tone={categoryTone(doc.enrichment.category)}
                    label={doc.enrichment.category}
                  />
                  <Badge
                    tone={processingStatusTone(doc.enrichment.status)}
                    label={doc.enrichment.status}
                  />
                </div>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}
