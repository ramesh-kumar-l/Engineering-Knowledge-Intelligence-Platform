import Link from "next/link";

import type { SearchResponse } from "@ekip/contracts";

import { Badge } from "@/components/badge";
import { entityKindTone } from "@/lib/format";

/** Presentational hybrid-search results: ranked chunks + a related-entities facet. */
export function SearchResults({ result }: { result: SearchResponse }) {
  if (result.chunks.length === 0 && result.entities.length === 0) {
    return (
      <p className="text-sm text-muted-foreground">
        No results for “{result.query}”. Try different terms, or embed the corpus from
        the Search Explorer.
      </p>
    );
  }

  return (
    <div className="space-y-6">
      <section>
        <h3 className="text-sm font-semibold">
          Results <span className="text-muted-foreground">({result.chunks.length})</span>
        </h3>
        {result.chunks.length === 0 ? (
          <p className="mt-3 text-sm text-muted-foreground">No matching passages.</p>
        ) : (
          <ul className="mt-3 space-y-3">
            {result.chunks.map((hit) => (
              <li
                key={hit.chunk_id}
                className="rounded-lg border border-border bg-card p-4"
              >
                <div className="flex items-start justify-between gap-3">
                  <p className="min-w-0 truncate text-sm font-medium">
                    {hit.url ? (
                      <a
                        href={hit.url}
                        className="hover:underline"
                        target="_blank"
                        rel="noreferrer"
                      >
                        {hit.title}
                      </a>
                    ) : (
                      hit.title
                    )}
                  </p>
                  <span className="shrink-0 text-xs text-muted-foreground">
                    score {hit.score.toFixed(4)}
                  </span>
                </div>
                <p className="mt-2 text-sm text-muted-foreground">{hit.snippet}</p>
                <div className="mt-2 flex gap-3 text-xs text-muted-foreground">
                  {hit.keyword_rank !== null ? (
                    <span>keyword #{hit.keyword_rank + 1}</span>
                  ) : null}
                  {hit.vector_rank !== null ? (
                    <span>vector #{hit.vector_rank + 1}</span>
                  ) : null}
                </div>
              </li>
            ))}
          </ul>
        )}
      </section>

      {result.entities.length > 0 ? (
        <section>
          <h3 className="text-sm font-semibold">Related entities</h3>
          <ul className="mt-3 divide-y divide-border rounded-lg border border-border bg-card px-4">
            {result.entities.map((entity) => (
              <li
                key={entity.key}
                className="flex items-center justify-between gap-3 py-2.5"
              >
                <Link
                  href={`/graph/entity?key=${encodeURIComponent(entity.key)}`}
                  className="min-w-0 truncate text-sm font-medium hover:underline"
                >
                  {entity.name}
                </Link>
                <Badge tone={entityKindTone(entity.kind)} label={entity.kind} />
              </li>
            ))}
          </ul>
        </section>
      ) : null}
    </div>
  );
}
