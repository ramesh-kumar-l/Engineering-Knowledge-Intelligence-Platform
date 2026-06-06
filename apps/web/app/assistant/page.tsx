import Link from "next/link";

import { fetchConversations } from "@/lib/api";
import { formatDate } from "@/lib/format";

import { askAction } from "./actions";

export const dynamic = "force-dynamic";

const EXAMPLES = [
  "How does the checkout service work?",
  "Who owns the billing API?",
  "What caused the latest incident?",
  "Why was this architecture chosen?",
];

export default async function AssistantWorkspacePage({
  searchParams,
}: {
  searchParams: { error?: string };
}) {
  const conversations = await fetchConversations();

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <h2 className="text-lg font-semibold tracking-tight">Assistant</h2>
          <p className="mt-1 text-sm text-muted-foreground">
            Ask about services, ownership, incidents and architecture. Every answer is
            built from retrieved evidence and carries its trust. (Phase 6)
          </p>
        </div>
        <Link href="/assistant/history" className="text-sm text-primary hover:underline">
          History →
        </Link>
      </div>

      {searchParams.error ? (
        <p className="rounded-md border border-danger/30 bg-danger/10 px-3 py-2 text-sm text-danger">
          {searchParams.error}
        </p>
      ) : null}

      <form action={askAction} className="space-y-3 rounded-lg border border-border bg-card p-5">
        <textarea
          name="question"
          rows={3}
          placeholder="Ask an engineering question…"
          className="w-full resize-none rounded-md border border-border bg-background px-3 py-2 text-sm"
          autoFocus
        />
        <div className="flex items-center justify-between">
          <span className="text-xs text-muted-foreground">
            Deterministic answers over your corpus — no data leaves the platform.
          </span>
          <button
            type="submit"
            className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-white hover:opacity-90"
          >
            Ask
          </button>
        </div>
      </form>

      <div className="flex flex-wrap gap-2">
        {EXAMPLES.map((example) => (
          <form key={example} action={askAction}>
            <input type="hidden" name="question" value={example} />
            <button
              type="submit"
              className="rounded-full border border-border px-3 py-1 text-xs text-muted-foreground hover:bg-muted"
            >
              {example}
            </button>
          </form>
        ))}
      </div>

      <section>
        <h3 className="text-sm font-semibold">Recent conversations</h3>
        {conversations.length === 0 ? (
          <p className="mt-2 text-sm text-muted-foreground">
            No conversations yet. Ask a question to get started.
          </p>
        ) : (
          <ul className="mt-3 divide-y divide-border rounded-lg border border-border bg-card">
            {conversations.slice(0, 8).map((c) => (
              <li key={c.id}>
                <Link
                  href={`/assistant/${c.id}`}
                  className="flex items-center justify-between gap-3 px-4 py-3 hover:bg-muted"
                >
                  <span className="min-w-0 truncate text-sm font-medium">{c.title}</span>
                  <span className="shrink-0 text-xs text-muted-foreground">
                    {c.message_count} msgs · {formatDate(c.updated_at)}
                  </span>
                </Link>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}
