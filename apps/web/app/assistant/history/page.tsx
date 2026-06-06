import Link from "next/link";

import { fetchConversations } from "@/lib/api";
import { formatDate } from "@/lib/format";

export const dynamic = "force-dynamic";

export default async function ConversationHistoryPage() {
  const conversations = await fetchConversations();

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <h2 className="text-lg font-semibold tracking-tight">Conversation History</h2>
          <p className="mt-1 text-sm text-muted-foreground">
            Every assistant conversation in this tenant, most recent first. (Phase 6)
          </p>
        </div>
        <Link href="/assistant" className="text-sm text-primary hover:underline">
          Ask →
        </Link>
      </div>

      <section className="rounded-lg border border-border bg-card p-5">
        <h3 className="text-sm font-semibold">
          Conversations{" "}
          <span className="text-muted-foreground">({conversations.length})</span>
        </h3>
        {conversations.length === 0 ? (
          <p className="mt-3 text-sm text-muted-foreground">
            No conversations yet. Ask the assistant a question to start one.
          </p>
        ) : (
          <table className="mt-4 w-full text-sm">
            <thead>
              <tr className="text-left text-xs text-muted-foreground">
                <th className="pb-2 font-medium">Conversation</th>
                <th className="pb-2 text-right font-medium">Messages</th>
                <th className="pb-2 text-right font-medium">Updated</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {conversations.map((c) => (
                <tr key={c.id}>
                  <td className="py-3">
                    <Link
                      href={`/assistant/${c.id}`}
                      className="font-medium hover:underline"
                    >
                      {c.title}
                    </Link>
                  </td>
                  <td className="py-3 text-right text-muted-foreground">
                    {c.message_count}
                  </td>
                  <td className="py-3 text-right text-muted-foreground">
                    {formatDate(c.updated_at)}
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
