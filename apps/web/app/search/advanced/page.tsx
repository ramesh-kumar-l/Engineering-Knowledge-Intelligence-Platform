import Link from "next/link";

import type { SearchMode } from "@ekip/contracts";

import { SearchResults } from "@/components/search-results";
import { fetchSearch } from "@/lib/api";

export const dynamic = "force-dynamic";

const MODES: { value: SearchMode; label: string; hint: string }[] = [
  { value: "hybrid", label: "Hybrid", hint: "keyword + vector (RRF)" },
  { value: "keyword", label: "Keyword", hint: "exact term match" },
  { value: "vector", label: "Vector", hint: "semantic similarity" },
];

export default async function AdvancedSearchPage({
  searchParams,
}: {
  searchParams: { q?: string; mode?: string };
}) {
  const query = searchParams.q?.trim() ?? "";
  const mode = (MODES.find((m) => m.value === searchParams.mode)?.value ??
    "hybrid") as SearchMode;
  const result = query ? await fetchSearch(query, mode) : null;

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <h2 className="text-lg font-semibold tracking-tight">Advanced search</h2>
          <p className="mt-1 text-sm text-muted-foreground">
            Choose how results are ranked and compare retrievers. (Phase 4)
          </p>
        </div>
        <Link href="/search" className="text-sm text-primary hover:underline">
          ← Simple
        </Link>
      </div>

      <form action="/search/advanced" className="space-y-3">
        <div className="flex gap-2">
          <input
            name="q"
            defaultValue={query}
            placeholder="Query…"
            className="flex-1 rounded-md border border-border bg-background px-3 py-2 text-sm"
            autoFocus
          />
          <button
            type="submit"
            className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-white hover:opacity-90"
          >
            Search
          </button>
        </div>
        <fieldset className="flex flex-wrap gap-4">
          {MODES.map((m) => (
            <label key={m.value} className="flex items-center gap-2 text-sm">
              <input
                type="radio"
                name="mode"
                value={m.value}
                defaultChecked={m.value === mode}
              />
              <span>{m.label}</span>
              <span className="text-xs text-muted-foreground">({m.hint})</span>
            </label>
          ))}
        </fieldset>
      </form>

      {result === null ? (
        <p className="text-sm text-muted-foreground">Enter a query to begin.</p>
      ) : (
        <SearchResults result={result} />
      )}
    </div>
  );
}
