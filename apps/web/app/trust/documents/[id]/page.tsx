import Link from "next/link";
import { notFound } from "next/navigation";

import { Badge } from "@/components/badge";
import { fetchTrustProfile } from "@/lib/api";
import { confidenceTone, formatAge, formatDate, freshnessTone } from "@/lib/format";

export const dynamic = "force-dynamic";

const SIGNAL_LABEL: Record<string, string> = {
  freshness: "Freshness",
  ownership: "Ownership",
  processed: "Processed",
  embedded: "Embedded",
  richness: "Richness",
};

export default async function TrustInspectorPage({
  params,
}: {
  params: { id: string };
}) {
  const profile = await fetchTrustProfile(params.id);
  if (!profile) notFound();

  // Bars are relative to the strongest contributing signal in this profile.
  const maxSignal = Math.max(...Object.values(profile.signals), 0.0001);

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <div>
        <Link href="/trust" className="text-sm text-primary hover:underline">
          ← Source Explorer
        </Link>
        <h2 className="mt-2 text-lg font-semibold tracking-tight">{profile.title}</h2>
        <p className="mt-1 text-sm text-muted-foreground">
          Trust Inspector — why this knowledge is (or is not) trusted. (Phase 5)
        </p>
      </div>

      <section className="grid grid-cols-1 gap-3 sm:grid-cols-3">
        <div className="rounded-lg border border-border bg-card p-4">
          <p className="text-xs text-muted-foreground">Confidence</p>
          <p className="mt-1 text-2xl font-semibold">{profile.confidence.toFixed(2)}</p>
          <div className="mt-2">
            <Badge
              tone={confidenceTone(profile.confidence_band)}
              label={profile.confidence_band}
            />
          </div>
        </div>
        <div className="rounded-lg border border-border bg-card p-4">
          <p className="text-xs text-muted-foreground">Freshness</p>
          <p className="mt-1 text-2xl font-semibold">{formatAge(profile.age_days)}</p>
          <div className="mt-2">
            <Badge
              tone={freshnessTone(profile.freshness_band)}
              label={profile.freshness_band}
            />
          </div>
        </div>
        <div className="rounded-lg border border-border bg-card p-4">
          <p className="text-xs text-muted-foreground">Ownership</p>
          <p className="mt-1 text-2xl font-semibold">
            {profile.ownership_known ? profile.owners.length : "—"}
          </p>
          <p className="mt-2 text-xs text-muted-foreground">
            {profile.ownership_known
              ? profile.owners.map((o) => o.name).join(", ")
              : "No owner attributed in the graph"}
          </p>
        </div>
      </section>

      <section className="rounded-lg border border-border bg-card p-5">
        <h3 className="text-sm font-semibold">Why this score</h3>
        <p className="mt-1 text-xs text-muted-foreground">
          Weighted signal contributions (sum to the confidence score).
        </p>
        <ul className="mt-3 space-y-2">
          {Object.entries(profile.signals).map(([key, value]) => (
            <li key={key} className="flex items-center gap-3 text-sm">
              <span className="w-24 shrink-0 text-muted-foreground">
                {SIGNAL_LABEL[key] ?? key}
              </span>
              <span className="h-2 flex-1 overflow-hidden rounded bg-muted">
                <span
                  className="block h-full bg-primary"
                  style={{ width: `${(value / maxSignal) * 100}%` }}
                />
              </span>
              <span className="w-12 shrink-0 text-right tabular-nums text-muted-foreground">
                {value.toFixed(2)}
              </span>
            </li>
          ))}
        </ul>
      </section>

      <section className="rounded-lg border border-border bg-card p-5">
        <h3 className="text-sm font-semibold">Source</h3>
        <dl className="mt-3 grid grid-cols-1 gap-x-6 gap-y-2 text-sm sm:grid-cols-2">
          <Row label="System" value={profile.source.source_type} />
          <Row label="External id" value={profile.source.external_id} />
          <Row label="Source updated" value={formatDate(profile.source.source_updated_at)} />
          <Row label="Ingested" value={formatDate(profile.source.ingested_at)} />
        </dl>
        {profile.source.url ? (
          <a
            href={profile.source.url}
            target="_blank"
            rel="noreferrer"
            className="mt-3 inline-block text-sm text-primary hover:underline"
          >
            Open at source →
          </a>
        ) : null}
      </section>

      <section className="rounded-lg border border-border bg-card p-5">
        <h3 className="text-sm font-semibold">
          Supporting evidence{" "}
          <span className="text-muted-foreground">({profile.evidence.length})</span>
        </h3>
        {profile.evidence.length === 0 ? (
          <p className="mt-3 text-sm text-muted-foreground">
            No excerpts — this document has not been processed into chunks yet.
          </p>
        ) : (
          <ul className="mt-3 space-y-3">
            {profile.evidence.map((item) => (
              <li
                key={item.chunk_id}
                className="rounded-md border border-border bg-background p-3 text-sm text-muted-foreground"
              >
                {item.snippet}
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between gap-3 border-b border-border/50 py-1">
      <dt className="text-muted-foreground">{label}</dt>
      <dd className="truncate text-right font-medium">{value}</dd>
    </div>
  );
}
