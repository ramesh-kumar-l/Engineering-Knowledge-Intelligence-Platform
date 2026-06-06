"use server";

import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";

import { createConnector, triggerSync } from "@/lib/api";

/** Create a GitHub connector (the implemented source) from the catalog form. */
export async function createConnectorAction(formData: FormData): Promise<void> {
  const result = await createConnector({
    source_type: "github",
    name: String(formData.get("name") ?? "").trim(),
    config: {
      owner: String(formData.get("owner") ?? "").trim(),
      repo: String(formData.get("repo") ?? "").trim(),
    },
    secret: String(formData.get("secret") ?? "").trim(),
  });
  if (!result.ok) {
    redirect(`/connectors?error=${encodeURIComponent(result.error ?? "Create failed")}`);
  }
  revalidatePath("/connectors");
  redirect("/connectors");
}

/** Trigger a sync run for a connector and refresh its detail view. */
export async function triggerSyncAction(formData: FormData): Promise<void> {
  const id = String(formData.get("connector_id"));
  const result = await triggerSync(id);
  revalidatePath(`/connectors/${id}`);
  if (!result.ok) {
    redirect(`/connectors/${id}?error=${encodeURIComponent(result.error ?? "Sync failed")}`);
  }
  redirect(`/connectors/${id}`);
}
