"use server";

import { redirect } from "next/navigation";

import { askAssistant } from "@/lib/api";

/**
 * Ask the assistant a question. Creates a new conversation, or continues an
 * existing one when a hidden ``conversation_id`` is supplied, then redirects to the
 * conversation thread. Failures bounce back with an error query param.
 */
export async function askAction(formData: FormData): Promise<void> {
  const question = String(formData.get("question") ?? "").trim();
  const conversationId = formData.get("conversation_id");
  const existing = conversationId ? String(conversationId) : undefined;

  if (!question) {
    redirect(`/assistant?error=${encodeURIComponent("Enter a question to ask.")}`);
  }

  const result = await askAssistant(question, existing);
  if (!result) {
    const back = existing ? `/assistant/${existing}` : "/assistant";
    redirect(`${back}?error=${encodeURIComponent("Assistant is unavailable.")}`);
  }

  redirect(`/assistant/${result.conversation_id}`);
}
