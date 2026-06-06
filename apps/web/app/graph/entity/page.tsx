import Link from "next/link";
import { notFound } from "next/navigation";

import { Badge } from "@/components/badge";
import { fetchGraphEntity } from "@/lib/api";
import { entityKindTone, relationshipLabel } from "@/lib/format";

export const dynamic = "force-dynamic";

export default async function EntityDetailPage({
  searchParams,
}: {
  searchParams: { key?: string };
}) {
  const key = searchParams.key;
  if (!key) notFound();

  const hood = await fetchGraphEntity(key);
  if (!hood) notFound();

  const { entity, neighbors } = hood;

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <Link href="/graph" className="text-xs text-muted-foreground hover:underline">
        ← Knowledge Graph
      </Link>

      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <h2 className="truncate text-lg font-semibold tracking-tight">
            {entity.name}
          </h2>
          {entity.summary ? (
            <p className="mt-1 text-sm text-muted-foreground">{entity.summary}</p>
          ) : null}
          {entity.url ? (
            <a
              href={entity.url}
              target="_blank"
              rel="noreferrer"
              className="mt-1 inline-block text-xs text-primary hover:underline"
            >
              Open source ↗
            </a>
          ) : null}
        </div>
        <div className="flex shrink-0 items-center gap-2">
          <Badge tone={entityKindTone(entity.kind)} label={entity.kind} />
          <span className="text-xs text-muted-foreground">{entity.source}</span>
        </div>
      </div>

      <section className="rounded-lg border border-border bg-card p-5">
        <h3 className="text-sm font-semibold">
          Relationships ({neighbors.length})
        </h3>
        {neighbors.length === 0 ? (
          <p className="mt-3 text-sm text-muted-foreground">
            No relationships for this entity yet.
          </p>
        ) : (
          <ul className="mt-4 space-y-2">
            {neighbors.map((n) => (
              <li
                key={`${n.type}-${n.direction}-${n.entity.key}`}
                className="flex items-center justify-between gap-3 text-sm"
              >
                <span className="text-muted-foreground">
                  {n.direction === "out" ? (
                    <>
                      {relationshipLabel(n.type)} →
                    </>
                  ) : (
                    <>← {relationshipLabel(n.type)}</>
                  )}
                </span>
                <Link
                  href={`/graph/entity?key=${encodeURIComponent(n.entity.key)}`}
                  className="min-w-0 flex-1 truncate text-right hover:underline"
                >
                  {n.entity.name}
                </Link>
                <Badge tone={entityKindTone(n.entity.kind)} label={n.entity.kind} />
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}
