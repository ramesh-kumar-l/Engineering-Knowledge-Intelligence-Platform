"use server";

import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";

import { triggerProcessing } from "@/lib/api";

/** Run the processing pipeline over pending documents, then refresh the dashboard. */
export async function runProcessingAction(): Promise<void> {
  const result = await triggerProcessing();
  revalidatePath("/processing");
  if (!result.ok) {
    redirect(`/processing?error=${encodeURIComponent(result.error ?? "Run failed")}`);
  }
  redirect("/processing");
}
