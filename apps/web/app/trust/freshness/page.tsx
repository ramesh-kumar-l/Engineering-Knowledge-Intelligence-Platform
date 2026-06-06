import Link from "next/link";

import { Badge } from "@/components/badge";
import { fetchFreshness } from "@/lib/api";
import { confidenceTone, formatAge, freshnessTone } from "@/lib/format";
import type { FreshnessBand } from "@ekip/contracts";

export const dynamic = "force-dynamic";

const BAND_LABEL: Record<FreshnessBand, string> = {
  fresh: "Fresh (≤30d)",
  recent: "Recent (≤90d)",
  aging: "Aging (≤1y)",
  stale: "Stale (>1y / unknown)",
};

export default async function FreshnessDashboardPage() {
  const summary = await fetchFreshness();
  const buckets = summary?.buckets ?? [];
  const total = summary?.total ?? 0;
  const stale = summary?.stale ?? [];

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <h2 className="text-lg font-semibold tracking-tight">Freshness Dashboard</h2>
          <p className="mt-1 text-sm text-muted-foreground">
            How current the engineering corpus is, by last-updated time. Stale knowledge
            is surfaced for review. (Phase 5)
          </p>
        </div>
        <Link href="/trust" className="text-sm text-primary hover:underline">
          Source Explorer →
        </Link>
      </div>

      <section className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        {buckets.map((bucket) => (
          <div
            key={bucket.band}
            className="rounded-lg border border-border bg-card p-4"
          >
            <p className="text-2xl font-semibold">{bucket.count}</p>
            <p className="mt-1 text-xs text-muted-foreground">
              {BAND_LABEL[bucket.band]}
            </p>
          </div>
        ))}
      </section>

      <section className="rounded-lg border border-border bg-card p-5">
        <h3 className="text-sm font-semibold">
          Needs attention{" "}
          <span className="text-muted-foreground">
            ({stale.length} of {total})
          </span>
        </h3>
        {stale.length === 0 ? (
          <p className="mt-3 text-sm text-muted-foreground">
            Nothing stale. The corpus is current.
          </p>
        ) : (
          <ul className="mt-3 divide-y divide-border">
            {stale.map((s) => (
              <li
                key={s.document_id}
                className="flex items-center justify-between gap-3 py-2.5"
              >
                <Link
                  href={`/trust/documents/${s.document_id}`}
                  className="min-w-0 truncate text-sm font-medium hover:underline"
                >
                  {s.title}
                </Link>
                <div className="flex shrink-0 items-center gap-3">
                  <span className="text-xs text-muted-foreground">
                    {formatAge(s.age_days)}
                  </span>
                  <Badge
                    tone={confidenceTone(s.confidence_band)}
                    label={s.confidence_band}
                  />
                  <Badge tone={freshnessTone(s.freshness_band)} label={s.freshness_band} />
                </div>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}
