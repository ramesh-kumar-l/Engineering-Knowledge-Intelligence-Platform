import Link from "next/link";
import { notFound } from "next/navigation";

import { AssistantAnswer } from "@/components/assistant-answer";
import { fetchConversation } from "@/lib/api";

import { askAction } from "../actions";

export const dynamic = "force-dynamic";

export default async function ConversationThreadPage({
  params,
  searchParams,
}: {
  params: { id: string };
  searchParams: { error?: string };
}) {
  const detail = await fetchConversation(params.id);
  if (detail === null) notFound();
  const { conversation, messages } = detail;

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <h2 className="truncate text-lg font-semibold tracking-tight">
            {conversation.title}
          </h2>
          <p className="mt-1 text-sm text-muted-foreground">
            {conversation.message_count} messages · Engineering Assistant
          </p>
        </div>
        <div className="flex shrink-0 gap-3 text-sm">
          <Link
            href={`/assistant/${conversation.id}/evidence`}
            className="text-primary hover:underline"
          >
            Evidence →
          </Link>
          <Link href="/assistant" className="text-muted-foreground hover:underline">
            New
          </Link>
        </div>
      </div>

      {searchParams.error ? (
        <p className="rounded-md border border-danger/30 bg-danger/10 px-3 py-2 text-sm text-danger">
          {searchParams.error}
        </p>
      ) : null}

      <ol className="space-y-4">
        {messages.map((message) =>
          message.role === "user" ? (
            <li key={message.id} className="flex justify-end">
              <p className="max-w-[85%] rounded-lg bg-primary/15 px-4 py-2 text-sm text-foreground">
                {message.content}
              </p>
            </li>
          ) : (
            <li
              key={message.id}
              className="rounded-lg border border-border bg-card p-5"
            >
              {message.answer ? (
                <AssistantAnswer answer={message.answer} />
              ) : (
                <p className="text-sm">{message.content}</p>
              )}
            </li>
          ),
        )}
      </ol>

      <form
        action={askAction}
        className="flex gap-2 rounded-lg border border-border bg-card p-3"
      >
        <input type="hidden" name="conversation_id" value={conversation.id} />
        <input
          name="question"
          placeholder="Ask a follow-up…"
          className="flex-1 rounded-md border border-border bg-background px-3 py-2 text-sm"
          autoFocus
        />
        <button
          type="submit"
          className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-white hover:opacity-90"
        >
          Ask
        </button>
      </form>
    </div>
  );
}
