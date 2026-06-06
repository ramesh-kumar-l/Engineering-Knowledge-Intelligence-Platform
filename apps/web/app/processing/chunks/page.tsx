import Link from "next/link";

import type { DocumentCategory } from "@ekip/contracts";

import { Badge } from "@/components/badge";
import { fetchProcessingStats } from "@/lib/api";
import { categoryTone } from "@/lib/format";

export const dynamic = "force-dynamic";

export default async function ChunkStatisticsPage() {
  const stats = await fetchProcessingStats();
  const distribution = stats?.category_distribution ?? {};
  const entries = Object.entries(distribution).sort((a, b) => b[1] - a[1]);
  const max = entries.reduce((m, [, n]) => Math.max(m, n), 0);

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <Link href="/processing" className="text-xs text-muted-foreground hover:underline">
        ← Processing
      </Link>

      <div>
        <h2 className="text-lg font-semibold tracking-tight">Chunk statistics</h2>
        <p className="mt-1 text-sm text-muted-foreground">
          Aggregate output of the processing pipeline across this tenant.
        </p>
      </div>

      <section className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <Stat label="Documents" value={stats?.documents_processed ?? 0} />
        <Stat label="Chunks" value={stats?.total_chunks ?? 0} />
        <Stat label="Total chars" value={stats?.total_chunk_chars ?? 0} />
        <Stat label="Avg chunk chars" value={stats?.avg_chunk_chars ?? 0} />
      </section>

      <section className="rounded-lg border border-border bg-card p-5">
        <h3 className="text-sm font-semibold">Category distribution</h3>
        {entries.length === 0 ? (
          <p className="mt-3 text-sm text-muted-foreground">
            No processed documents yet.
          </p>
        ) : (
          <ul className="mt-4 space-y-3">
            {entries.map(([category, count]) => (
              <li key={category} className="flex items-center gap-3">
                <span className="w-28 shrink-0">
                  <Badge
                    tone={categoryTone(category as DocumentCategory)}
                    label={category}
                  />
                </span>
                <div className="h-2 flex-1 rounded-full bg-muted">
                  <div
                    className="h-2 rounded-full bg-primary"
                    style={{ width: `${max ? (count / max) * 100 : 0}%` }}
                  />
                </div>
                <span className="w-8 text-right text-sm text-muted-foreground">
                  {count}
                </span>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-lg border border-border bg-card p-3 text-center">
      <p className="text-lg font-semibold">{value}</p>
      <p className="text-xs text-muted-foreground">{label}</p>
    </div>
  );
}
