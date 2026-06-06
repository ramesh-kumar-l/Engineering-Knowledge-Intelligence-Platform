import Link from "next/link";

import { SearchResults } from "@/components/search-results";
import { fetchSearch } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function GlobalSearchPage({
  searchParams,
}: {
  searchParams: { q?: string };
}) {
  const query = searchParams.q?.trim() ?? "";
  const result = query ? await fetchSearch(query, "hybrid") : null;

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <h2 className="text-lg font-semibold tracking-tight">Search</h2>
          <p className="mt-1 text-sm text-muted-foreground">
            Hybrid retrieval over embedded chunks and the knowledge graph. (Phase 4)
          </p>
        </div>
        <Link
          href="/search/advanced"
          className="text-sm text-primary hover:underline"
        >
          Advanced →
        </Link>
      </div>

      <form action="/search" className="flex gap-2">
        <input
          name="q"
          defaultValue={query}
          placeholder="Ask anything — service, incident, owner…"
          className="flex-1 rounded-md border border-border bg-background px-3 py-2 text-sm"
          autoFocus
        />
        <button
          type="submit"
          className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-white hover:opacity-90"
        >
          Search
        </button>
      </form>

      {result === null ? (
        <p className="text-sm text-muted-foreground">
          Enter a query to search the engineering corpus. Need to build the index?{" "}
          <Link href="/search/explorer" className="text-primary hover:underline">
            Open the Search Explorer
          </Link>
          .
        </p>
      ) : (
        <SearchResults result={result} />
      )}
    </div>
  );
}
