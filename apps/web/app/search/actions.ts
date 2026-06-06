"use server";

import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";

import { triggerEmbedding } from "@/lib/api";

/** Embed processed chunks into the vector store, then refresh the Search Explorer. */
export async function embedAction(): Promise<void> {
  const result = await triggerEmbedding();
  revalidatePath("/search/explorer");
  if (!result.ok) {
    redirect(
      `/search/explorer?error=${encodeURIComponent(result.error ?? "Embedding failed")}`,
    );
  }
  redirect("/search/explorer");
}
