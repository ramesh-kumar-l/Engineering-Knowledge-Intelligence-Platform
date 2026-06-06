import Link from "next/link";

import { Badge } from "@/components/badge";
import { fetchTrustSources } from "@/lib/api";
import { confidenceTone, formatAge, freshnessTone } from "@/lib/format";

export const dynamic = "force-dynamic";

export default async function SourceExplorerPage({
  searchParams,
}: {
  searchParams: { source_type?: string };
}) {
  const sourceType = searchParams.source_type;
  const sources = await fetchTrustSources(sourceType);

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <h2 className="text-lg font-semibold tracking-tight">Source Explorer</h2>
          <p className="mt-1 text-sm text-muted-foreground">
            Every ingested source with its provenance and trust — confidence,
            freshness and ownership, computed from current state. (Phase 5)
          </p>
        </div>
        <Link href="/trust/freshness" className="text-sm text-primary hover:underline">
          Freshness →
        </Link>
      </div>

      <section className="rounded-lg border border-border bg-card p-5">
        <h3 className="text-sm font-semibold">
          Sources <span className="text-muted-foreground">({sources.length})</span>
        </h3>
        {sources.length === 0 ? (
          <p className="mt-3 text-sm text-muted-foreground">
            No sources yet. Add a connector and run a sync to ingest documents.
          </p>
        ) : (
          <table className="mt-4 w-full text-sm">
            <thead>
              <tr className="text-left text-xs text-muted-foreground">
                <th className="pb-2 font-medium">Document</th>
                <th className="pb-2 font-medium">Source</th>
                <th className="pb-2 font-medium">Confidence</th>
                <th className="pb-2 font-medium">Freshness</th>
                <th className="pb-2 font-medium">Owner</th>
                <th className="pb-2 text-right font-medium">Updated</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {sources.map((s) => (
                <tr key={s.document_id}>
                  <td className="py-3">
                    <Link
                      href={`/trust/documents/${s.document_id}`}
                      className="font-medium hover:underline"
                    >
                      {s.title}
                    </Link>
                  </td>
                  <td className="py-3 text-muted-foreground">{s.source_type}</td>
                  <td className="py-3">
                    <Badge
                      tone={confidenceTone(s.confidence_band)}
                      label={`${s.confidence_band} ${s.confidence.toFixed(2)}`}
                    />
                  </td>
                  <td className="py-3">
                    <Badge
                      tone={freshnessTone(s.freshness_band)}
                      label={s.freshness_band}
                    />
                  </td>
                  <td className="py-3 text-muted-foreground">
                    {s.has_owner ? "known" : "—"}
                  </td>
                  <td className="py-3 text-right text-muted-foreground">
                    {formatAge(s.age_days)}
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
